"""The facts object: every number pre-formatted as a string by Python, for the model to quote."""

from __future__ import annotations

from typing import Any

from margin_watch.formatting import format_date, format_money, format_pct, format_pts
from margin_watch.labels import WHAT_TO_CHECK
from margin_watch.models import JobAssessment, RunReport, Status


def _job_facts(assessment: JobAssessment) -> dict[str, str]:
    job = assessment.job
    facts = {
        "job_id": job.id,
        "name": job.name,
        "client": job.client,
        "site": job.site,
        "project_manager": job.project_manager,
        "status": assessment.status.value,
    }
    metrics = assessment.metrics
    if metrics is None or job.percent_complete is None:
        facts["review_problem"] = assessment.reason
        facts["what_to_check"] = WHAT_TO_CHECK.get(assessment.review_code or "", "")
        return facts
    facts |= {
        "percent_complete": format_pct(job.percent_complete),
        "quoted_margin": format_pct(metrics.quoted_margin_pct),
        "forecast_margin": format_pct(metrics.forecast_margin_pct),
        "margin_erosion": format_pts(metrics.margin_erosion_pts),
        "dollars_at_risk": format_money(metrics.dollars_at_risk),
    }
    driver = next((c for c in metrics.cost_centres if c.name == assessment.main_driver), None)
    if driver is not None:
        facts["main_driver"] = driver.name
        facts["main_driver_overrun"] = format_money(driver.overrun_dollars)
        if driver.overrun_pct is not None:
            facts["main_driver_overrun_pct"] = format_pct(driver.overrun_pct)
    facts["reason"] = assessment.reason
    return facts


def build_facts(report: RunReport) -> dict[str, Any]:
    """`{"overview": {...}, "jobs": {job_id: {...}}}` for every job that isn't ON_TRACK."""
    portfolio = report.portfolio
    counts = portfolio.counts
    flagged = [a for a in report.assessments if a.status != Status.ON_TRACK]
    average = portfolio.average_forecast_margin_pct
    overview = {
        "run_date": format_date(report.as_of),
        "total_jobs": str(portfolio.total_jobs),
        "jobs_needing_action": str(portfolio.jobs_needing_action),
        "jobs_to_review": str(portfolio.jobs_to_review),
        "total_dollars_at_risk": format_money(portfolio.total_dollars_at_risk),
        "average_forecast_margin": "not available" if average is None else format_pct(average),
        "counts": {
            "loss": str(counts[Status.LOSS]),
            "at_risk": str(counts[Status.AT_RISK]),
            "watch": str(counts[Status.WATCH]),
            "needs_review": str(counts[Status.NEEDS_REVIEW]),
            "on_track": str(counts[Status.ON_TRACK]),
        },
        "flagged_jobs": [
            {
                "job_id": a.job.id,
                "name": a.job.name,
                "project_manager": a.job.project_manager,
                "status": a.status.value,
            }
            for a in flagged
        ],
    }
    return {"overview": overview, "jobs": {a.job.id: _job_facts(a) for a in flagged}}
