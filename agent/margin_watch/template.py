"""The template summary: plain wording built by code. Used with --ai off and on every fallback."""

from __future__ import annotations

from collections.abc import Sequence

from margin_watch.calc import ZERO
from margin_watch.formatting import format_money
from margin_watch.models import JobAssessment, PortfolioSummary, Status


def join_words(items: Sequence[str]) -> str:
    """`A`, `A and B`, `A, B and C`."""
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def _clause(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _overview(portfolio: PortfolioSummary) -> str:
    counts = portfolio.counts
    parts = [
        _clause(counts[Status.LOSS], "is heading for a loss", "are heading for a loss"),
        _clause(counts[Status.AT_RISK], "is at risk", "are at risk"),
        _clause(counts[Status.WATCH], "is on watch", "are on watch"),
        _clause(counts[Status.NEEDS_REVIEW], "needs a data check", "need a data check"),
        _clause(counts[Status.ON_TRACK], "is on track", "are on track"),
    ]
    present = [part for part in parts if not part.startswith("0 ")]
    total = portfolio.total_jobs
    if total == 0:
        return "There are no jobs in this run."
    text = f"Of {_clause(total, 'job', 'jobs')}, {join_words(present)}."
    if portfolio.total_dollars_at_risk > ZERO:
        text += f" Forecast overruns add up to {format_money(portfolio.total_dollars_at_risk)}."
    return text


def _named(assessment: JobAssessment) -> str:
    job = assessment.job
    return f"{job.id} {job.name} ({job.project_manager})"


def template_summary(assessments: Sequence[JobAssessment], portfolio: PortfolioSummary) -> str:
    """Overview, one paragraph per LOSS / AT_RISK job, then WATCH and NEEDS_REVIEW jobs."""
    paragraphs = [_overview(portfolio)]
    for assessment in assessments:
        if assessment.status in (Status.LOSS, Status.AT_RISK):
            job = assessment.job
            paragraphs.append(
                f"Call {job.project_manager} about {job.id} {job.name}. {assessment.reason}"
            )
    watch = [_named(a) for a in assessments if a.status == Status.WATCH]
    review = [_named(a) for a in assessments if a.status == Status.NEEDS_REVIEW]
    closing = []
    if watch:
        closing.append(f"On watch: {join_words(watch)}.")
    if review:
        closing.append(f"Data to check in Simpro: {join_words(review)}.")
    if closing:
        paragraphs.append(" ".join(closing))
    return "\n\n".join(paragraphs)
