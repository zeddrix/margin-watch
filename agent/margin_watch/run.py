"""One morning run: assess, summarise, then write the run JSON, index, Excel and email draft."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from margin_watch.calc import summarise_portfolio
from margin_watch.email_graph import build_email_html, build_sendmail_payload
from margin_watch.mailer import DryRunMailer, EmailDraft
from margin_watch.models import (
    STATUS_ORDER,
    CostCentreResult,
    JobAssessment,
    RunReport,
    Snapshot,
    Summary,
    Thresholds,
)
from margin_watch.report_excel import write_excel
from margin_watch.status import assess_jobs
from margin_watch.template import template_summary

SCHEMA_VERSION = 1
_CENTS = Decimal("0.01")
_FOUR_DP = Decimal("0.0001")


@dataclass(frozen=True)
class RunOutputs:
    run_json: Path
    index_json: Path
    excel: Path
    graph_json: Path
    preview_html: Path

    def all(self) -> tuple[Path, ...]:
        return (self.run_json, self.index_json, self.excel, self.graph_json, self.preview_html)


def build_report(
    snapshot: Snapshot,
    *,
    source_name: str,
    as_of: date,
    generated_at: datetime,
    thresholds: Thresholds,
    summary: Summary | None = None,
    sample_data: bool = True,
) -> RunReport:
    """Assess every job. Without a summary, the template summary is used (`--ai off`)."""
    assessments = assess_jobs(snapshot.jobs, thresholds)
    portfolio = summarise_portfolio(assessments)
    if summary is None:
        summary = Summary(
            text=template_summary(assessments, portfolio),
            source="template",
            provider="none",
            model=None,
            fallback_reason="ai_off",
        )
    return RunReport(
        schema_version=SCHEMA_VERSION,
        as_of=as_of,
        generated_at=generated_at,
        source_name=source_name,
        sample_data=sample_data,
        thresholds=thresholds,
        assessments=tuple(assessments),
        portfolio=portfolio,
        summary=summary,
    )


# --- run JSON -----------------------------------------------------------------------------------
# JSON carries numbers for the dashboard: money to cents, percentages and points to 4 dp.


def _number(value: Decimal | None, step: Decimal) -> float | None:
    if value is None:
        return None
    return float(value.quantize(step, rounding=ROUND_HALF_UP)) + 0.0  # + 0.0 drops "-0.0"


def money(value: Decimal | None) -> float | None:
    return _number(value, _CENTS)


def pct(value: Decimal | None) -> float | None:
    return _number(value, _FOUR_DP)


def _job_json(assessment: JobAssessment) -> dict[str, Any]:
    job = assessment.job
    metrics = assessment.metrics
    results: dict[str, CostCentreResult] = (
        {} if metrics is None else {c.name: c for c in metrics.cost_centres}
    )
    centres = []
    for centre in job.cost_centres:
        result = results.get(centre.name)
        centres.append(
            {
                "name": centre.name,
                "estimated_cost": money(centre.estimated_cost),
                "actual_cost_to_date": money(centre.actual_cost_to_date),
                "forecast_at_completion": money(result.forecast_at_completion) if result else None,
                "overrun_dollars": money(result.overrun_dollars) if result else None,
                "overrun_pct": pct(result.overrun_pct) if result else None,
                "estimated_hours": money(centre.estimated_hours),
                "actual_hours": money(centre.actual_hours),
                "hourly_rate": money(centre.hourly_rate),
            }
        )
    return {
        "id": job.id,
        "name": job.name,
        "client": job.client,
        "site": job.site,
        "stage": job.stage,
        "project_manager": job.project_manager,
        "quoted_sell_ex_gst": money(job.quoted_sell_ex_gst),
        "percent_complete": pct(job.percent_complete),
        "status": assessment.status.value,
        "reason": assessment.reason,
        "review_code": assessment.review_code,
        "main_driver": assessment.main_driver,
        "estimated_total": money(metrics.estimated_total) if metrics else None,
        "forecast_total": money(metrics.forecast_total) if metrics else None,
        "quoted_margin_pct": pct(metrics.quoted_margin_pct) if metrics else None,
        "forecast_margin_pct": pct(metrics.forecast_margin_pct) if metrics else None,
        "margin_erosion_pts": pct(metrics.margin_erosion_pts) if metrics else None,
        "dollars_at_risk": money(metrics.dollars_at_risk) if metrics else None,
        "cost_centres": centres,
    }


def report_to_json(report: RunReport) -> dict[str, Any]:
    """The run JSON document (schema version 1). See docs/acceptance-criteria.md, AC-34/35."""
    thresholds = report.thresholds
    portfolio = report.portfolio
    summary = report.summary
    return {
        "schema_version": report.schema_version,
        "as_of": report.as_of.isoformat(),
        "generated_at": report.generated_at.isoformat(timespec="seconds"),
        "source": {
            "kind": "sample_file",
            "name": report.source_name,
            "sample_data": report.sample_data,
        },
        "thresholds": {
            "at_risk_margin_pct": pct(thresholds.at_risk_margin_pct),
            "at_risk_erosion_pts": pct(thresholds.at_risk_erosion_pts),
            "watch_erosion_pts": pct(thresholds.watch_erosion_pts),
            "watch_overrun_pct": pct(thresholds.watch_overrun_pct),
        },
        "counts": {status.value: portfolio.counts[status] for status in STATUS_ORDER},
        "portfolio": {
            "total_jobs": portfolio.total_jobs,
            "jobs_needing_action": portfolio.jobs_needing_action,
            "jobs_to_review": portfolio.jobs_to_review,
            "total_dollars_at_risk": money(portfolio.total_dollars_at_risk),
            "average_forecast_margin_pct": pct(portfolio.average_forecast_margin_pct),
        },
        "jobs": [_job_json(a) for a in report.assessments],
        "summary": {
            "text": summary.text,
            "source": summary.source,
            "provider": summary.provider,
            "model": summary.model,
            "fallback_reason": summary.fallback_reason,
            "rejected_tokens": list(summary.rejected_tokens),
        },
    }


def dump_json(document: Any) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def _index_entry(document: dict[str, Any], file_name: str) -> dict[str, Any]:
    return {
        "as_of": document["as_of"],
        "file": file_name,
        "generated_at": document["generated_at"],
        "counts": document["counts"],
        "jobs_needing_action": document["portfolio"]["jobs_needing_action"],
        "total_dollars_at_risk": document["portfolio"]["total_dollars_at_risk"],
        "summary_source": document["summary"]["source"],
    }


def update_index(runs_dir: Path, document: dict[str, Any], file_name: str) -> Path:
    """Add or replace this run's entry in runs/index.json, newest first."""
    path = runs_dir / "index.json"
    runs: list[dict[str, Any]] = []
    if path.exists():
        runs = [r for r in json.loads(path.read_text(encoding="utf-8"))["runs"]]
    runs = [r for r in runs if r["as_of"] != document["as_of"]]
    runs.append(_index_entry(document, file_name))
    runs.sort(key=lambda r: str(r["as_of"]), reverse=True)
    path.write_text(dump_json({"schema_version": SCHEMA_VERSION, "runs": runs}), encoding="utf-8")
    return path


def write_outputs(report: RunReport, output_dir: Path, recipient: str) -> RunOutputs:
    """Write the run JSON, update the index, write the Excel report and the email draft."""
    stamp = report.as_of.isoformat()
    runs_dir = output_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    document = report_to_json(report)
    run_json = runs_dir / f"{stamp}.json"
    run_json.write_text(dump_json(document), encoding="utf-8")
    index_json = update_index(runs_dir, document, run_json.name)
    excel = write_excel(report, output_dir / f"margin-report-{stamp}.xlsx")
    draft = EmailDraft(
        as_of=report.as_of,
        payload=build_sendmail_payload(report, recipient),
        html=build_email_html(report),
    )
    receipt = DryRunMailer(output_dir / "email").send(draft)
    return RunOutputs(
        run_json=run_json,
        index_json=index_json,
        excel=excel,
        graph_json=receipt.payload_path,
        preview_html=receipt.preview_path,
    )
