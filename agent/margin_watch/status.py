"""Job status rules. See docs/spec.md, "Status rules"."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from margin_watch.calc import HUNDRED, ZERO, compute_metrics, main_driver
from margin_watch.formatting import format_money, format_pct, format_pts
from margin_watch.models import (
    STATUS_ORDER,
    CostCentreResult,
    Job,
    JobAssessment,
    ReviewProblem,
    Status,
    Thresholds,
)

FLAGGED = frozenset({Status.LOSS, Status.AT_RISK, Status.WATCH})
_COST_FIELDS = (
    ("estimated_cost", "estimated cost"),
    ("actual_cost_to_date", "actual cost to date"),
)


def _cost_problem(job: Job, missing: bool) -> ReviewProblem | None:
    for centre in job.cost_centres:
        for field, label in _COST_FIELDS:
            value: Decimal | None = getattr(centre, field)
            if missing and value is None:
                return ReviewProblem(
                    code="missing_cost", reason=f"{centre.name} {label} is missing."
                )
            if not missing and value is not None and value < ZERO:
                return ReviewProblem(
                    code="negative_cost",
                    reason=f"{centre.name} {label} is negative ({format_money(value)}).",
                )
    return None


def review_problem(job: Job) -> ReviewProblem | None:
    """The first data problem that makes a job NEEDS_REVIEW, or None. Order: docs/spec.md."""
    if not job.cost_centres:
        return ReviewProblem(code="no_cost_centres", reason="Job has no cost centres.")
    sell = job.quoted_sell_ex_gst
    if sell is None:
        return ReviewProblem(code="missing_sell", reason="Quoted sell price is missing.")
    if sell <= ZERO:
        return ReviewProblem(
            code="non_positive_sell",
            reason=f"Quoted sell price is {format_money(sell)}; it must be above $0.",
        )
    problem = _cost_problem(job, missing=True) or _cost_problem(job, missing=False)
    if problem:
        return problem
    percent = job.percent_complete
    if percent is None:
        return ReviewProblem(
            code="missing_percent_complete",
            reason="Percent complete is missing, so the forecast can't be worked out.",
        )
    if percent < ZERO or percent > HUNDRED:
        return ReviewProblem(
            code="percent_out_of_range",
            reason=f"Percent complete is {format_pct(percent)}, outside 0 to 100%.",
        )
    actuals = [c.actual_cost_to_date or ZERO for c in job.cost_centres]
    if percent == ZERO and any(a > ZERO for a in actuals):
        spent = format_money(sum(actuals, ZERO))
        return ReviewProblem(
            code="zero_percent_with_costs",
            reason=f"Percent complete is 0% but {spent} has been spent.",
        )
    return None


def _overrun_phrase(centre: CostCentreResult) -> str:
    pct = "" if centre.overrun_pct is None else f" ({format_pct(centre.overrun_pct)})"
    return f"projected {format_money(centre.overrun_dollars)}{pct} over estimate"


def assess_job(job: Job, thresholds: Thresholds) -> JobAssessment:
    """Status, reason, main driver and metrics for one job."""
    problem = review_problem(job)
    if problem is not None:
        return JobAssessment(
            job=job,
            status=Status.NEEDS_REVIEW,
            reason=problem.reason,
            review_code=problem.code,
            main_driver=None,
            metrics=None,
        )

    metrics = compute_metrics(job)
    forecast = metrics.forecast_margin_pct
    quoted = metrics.quoted_margin_pct
    erosion = metrics.margin_erosion_pts
    over_limit = [
        c
        for c in metrics.cost_centres
        if c.overrun_pct is not None and c.overrun_pct >= thresholds.watch_overrun_pct
    ]
    named: str | None = None

    if forecast < ZERO:
        status = Status.LOSS
        reason = (
            f"Heading for a loss: forecast margin {format_pct(forecast)} "
            f"against {format_pct(quoted)} quoted."
        )
    elif forecast < thresholds.at_risk_margin_pct:
        status = Status.AT_RISK
        reason = (
            f"Forecast margin {format_pct(forecast)} is below the "
            f"{format_pct(thresholds.at_risk_margin_pct)} floor (quoted {format_pct(quoted)})."
        )
    elif erosion >= thresholds.at_risk_erosion_pts:
        status = Status.AT_RISK
        reason = (
            f"Margin has eroded {format_pts(erosion)} since quote, past the "
            f"{format_pts(thresholds.at_risk_erosion_pts)} limit."
        )
    elif erosion >= thresholds.watch_erosion_pts:
        status = Status.WATCH
        reason = f"Margin has eroded {format_pts(erosion)} since quote."
    elif over_limit:
        status = Status.WATCH
        worst = min(over_limit, key=lambda c: (-(c.overrun_pct or ZERO), c.name))
        named = worst.name
        reason = f"{worst.name} is {_overrun_phrase(worst)}."
    else:
        status = Status.ON_TRACK
        reason = (
            f"Forecast margin {format_pct(forecast)} against {format_pct(quoted)} quoted, "
            "within thresholds."
        )

    driver = main_driver(metrics) if status in FLAGGED else None
    if driver is not None and driver != named:
        centre = next(c for c in metrics.cost_centres if c.name == driver)
        reason += f" Main driver: {driver}, {_overrun_phrase(centre)}."

    return JobAssessment(
        job=job,
        status=status,
        reason=reason,
        review_code=None,
        main_driver=driver,
        metrics=metrics,
    )


def _sort_key(assessment: JobAssessment) -> tuple[int, Decimal, str]:
    at_risk = assessment.metrics.dollars_at_risk if assessment.metrics else ZERO
    return (STATUS_ORDER.index(assessment.status), -at_risk, assessment.job.id)


def sort_assessments(assessments: Sequence[JobAssessment]) -> list[JobAssessment]:
    """Risk order: status, then dollars at risk descending, then job id."""
    return sorted(assessments, key=_sort_key)


def assess_jobs(jobs: Sequence[Job], thresholds: Thresholds) -> list[JobAssessment]:
    """Assess every job and return them in risk order."""
    return sort_assessments([assess_job(job, thresholds) for job in jobs])
