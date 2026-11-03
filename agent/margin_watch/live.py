"""The live dry run behind the dashboard's "Run this morning's check" button.

It runs the real pipeline step by step and yields plain-English events for the screen. Every
number in the events is formatted by Python. Nothing is sent; only the offline demo AI is used.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from margin_watch.config import REPO_ROOT, load_settings, load_thresholds
from margin_watch.demo_model import DEMO_MODEL, DemoModelClient
from margin_watch.email_graph import build_subject
from margin_watch.formatting import format_money
from margin_watch.labels import PROVIDER_NAMES
from margin_watch.models import Provider, RunReport, Status
from margin_watch.report_excel import write_excel
from margin_watch.run import build_report, excel_path, write_email, write_run_files
from margin_watch.sources import SampleFileSource, SourceError
from margin_watch.summarise import summarise_detailed
from margin_watch.template import join_words

SAMPLE_DIR = REPO_ROOT / "data" / "sample"
LIVE_AI = ("demo", "demo-bad")
STEPS: tuple[tuple[str, str], ...] = (
    ("read", "Reading the jobs"),
    ("maths", "Doing the maths"),
    ("review", "Catching bad data"),
    ("summary", "AI writes the summary, and every number is checked"),
    ("excel", "Saving the Excel report"),
    ("email", "Drafting the morning email"),
    ("dashboard", "Updating the dashboard"),
)
_TALLY = (
    (Status.LOSS, "heading for a loss", "heading for a loss"),
    (Status.AT_RISK, "at risk", "at risk"),
    (Status.WATCH, "on watch", "on watch"),
    (Status.ON_TRACK, "on track", "on track"),
)


def sample_dates(sample_dir: Path = SAMPLE_DIR) -> list[str]:
    """ISO dates that have a sample file, oldest first."""
    return sorted(p.stem.removeprefix("jobs-") for p in sample_dir.glob("jobs-????-??-??.json"))


def _step(step: str, state: str, detail: str | None = None, **data: Any) -> dict[str, Any]:
    event: dict[str, Any] = {"type": "step", "step": step, "state": state}
    if detail is not None:
        event["detail"] = detail
    if data:
        event["data"] = data
    return event


def _jobs_word(count: int) -> str:
    return f"{count} job" if count == 1 else f"{count} jobs"


def _maths_detail(report: RunReport) -> str:
    counts = report.portfolio.counts
    assessed = report.portfolio.total_jobs - counts[Status.NEEDS_REVIEW]
    parts = [f"{counts[s]} {label}" for s, label, _ in _TALLY if counts[s]]
    return (
        f"Worked out the quoted and forecast margin for {_jobs_word(assessed)}: "
        f"{join_words(parts)}."
    )


def _review_detail(count: int) -> str:
    if count == 0:
        return "Every job's data looked complete, so nothing needs a data check."
    verb = "has" if count == 1 else "have"
    pronoun = "It's" if count == 1 else "They're"
    return (
        f"{_jobs_word(count)} {verb} missing or wrong data. "
        f"{pronoun} flagged for review instead of guessed."
    )


def run_live(
    *,
    as_of: str,
    ai: str,
    output_dir: Path,
    source: Path | None = None,
    pace: float = 0.9,
    sleep: Callable[[float], None] = time.sleep,
    now: datetime | None = None,
) -> Iterator[dict[str, Any]]:
    """Run the morning check for `as_of`, yielding start, step and done (or error) events."""
    if ai not in LIVE_AI:
        raise ValueError(f"The live run only uses the offline demo AI, not {ai!r}")
    settings = load_settings()
    source = source or SAMPLE_DIR / f"jobs-{as_of}.json"
    moment = now or datetime.now(ZoneInfo(settings.timezone)).replace(microsecond=0)

    def pause() -> None:
        if pace > 0:
            sleep(pace)

    yield {
        "type": "start",
        "dry_run": True,
        "ai": ai,
        "as_of": as_of,
        "steps": [{"id": step_id, "title": title} for step_id, title in STEPS],
    }
    current = "read"
    try:
        yield _step("read", "running")
        snapshot = SampleFileSource(source).load()
        yield _step(
            "read",
            "done",
            f"Read {_jobs_word(len(snapshot.jobs))} from {source.name} "
            "(sample data shaped like a Simpro export).",
            jobs=len(snapshot.jobs),
            source=source.name,
        )
        pause()

        current = "maths"
        yield _step("maths", "running")
        report = build_report(
            snapshot,
            source_name=source.name,
            as_of=date.fromisoformat(as_of),
            generated_at=moment,
            thresholds=load_thresholds(),
        )
        yield _step(
            "maths",
            "done",
            _maths_detail(report),
            counts={s.value: n for s, n in report.portfolio.counts.items()},
            dollars_at_risk=format_money(report.portfolio.total_dollars_at_risk),
        )
        pause()

        current = "review"
        yield _step("review", "running")
        flagged = [a for a in report.assessments if a.status == Status.NEEDS_REVIEW]
        yield _step(
            "review",
            "done",
            _review_detail(len(flagged)),
            jobs=[{"id": a.job.id, "name": a.job.name, "problem": a.reason} for a in flagged],
        )
        pause()

        current = "summary"
        yield _step("summary", "running")
        provider: Provider = "demo-bad" if ai == "demo-bad" else "demo"
        outcome = summarise_detailed(
            report, DemoModelClient(bad=ai == "demo-bad"), provider=provider, model=DEMO_MODEL
        )
        outcome_summary = outcome.summary
        report = report.model_copy(update={"summary": outcome_summary})
        writer = PROVIDER_NAMES[ai]
        checks = [{"token": c.token, "ok": c.ok} for c in outcome.checks]
        rejected = list(outcome_summary.rejected_tokens)
        if outcome_summary.source == "ai_verified":
            state = "done"
            detail = (
                f"{writer} wrote the summary. All {len(checks)} numbers in it match the "
                "calculations, so it was approved."
            )
        else:
            state = "warning"
            bad = join_words(rejected) or "a problem"
            verb = "isn't" if len(rejected) <= 1 else "aren't"
            detail = (
                f"{writer} wrote a summary, but {bad} {verb} in the calculations. The answer "
                "was rejected and the safe template summary was used instead."
            )
        yield _step(
            "summary",
            state,
            detail,
            verified=outcome_summary.source == "ai_verified",
            writer=writer,
            checks=checks,
            rejected=rejected,
        )
        pause()

        current = "excel"
        yield _step("excel", "running")
        excel = write_excel(report, excel_path(report, output_dir))
        yield _step(
            "excel",
            "done",
            f"Saved {excel.name} with three sheets: Summary, Jobs and Cost centres.",
            file=excel.name,
            href=f"/files/{excel.name}",
        )
        pause()

        current = "email"
        yield _step("email", "running")
        receipt = write_email(report, output_dir, settings.email_to)
        subject = build_subject(report)
        yield _step(
            "email",
            "done",
            f"Drafted the email to {settings.email_to}: “{subject}”. "
            "Dry run, so it was saved, not sent.",
            to=settings.email_to,
            subject=subject,
            href=f"/files/email/{receipt.preview_path.name}",
        )
        pause()

        current = "dashboard"
        yield _step("dashboard", "running")
        run_json, _ = write_run_files(report, output_dir)
        yield _step(
            "dashboard", "done", "Saved the run so the dashboard can show it.", file=run_json.name
        )
        pause()
    except SourceError as error:
        yield {"type": "error", "step": current, "message": f"Invalid input file: {error}"}
        return
    except Exception as error:  # the stream boundary: show the problem on screen, never hide it
        yield {"type": "error", "step": current, "message": f"{type(error).__name__}: {error}"}
        return
    yield {"type": "done", "as_of": as_of, "sent": False, "file": run_json.name}
