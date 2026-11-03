"""Pure margin calculations. See docs/spec.md, "Formulas".

Percentages are in percent units (20 = 20%). Nothing is rounded here; see formatting.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from margin_watch.models import (
    STATUS_ORDER,
    CostCentre,
    CostCentreResult,
    Job,
    JobAssessment,
    JobMetrics,
    PortfolioSummary,
    Status,
)

HUNDRED = Decimal(100)
ZERO = Decimal(0)


def _known(value: Decimal | None, what: str) -> Decimal:
    # Precondition, not a code path: callers run status.review_problem() first, so a job with a
    # missing value never reaches the maths. Nothing is ever defaulted or guessed here.
    assert value is not None, f"{what} is missing; run the NEEDS_REVIEW checks first"
    return value


def forecast_at_completion(cost_centre: CostCentre, percent_complete: Decimal) -> Decimal:
    """Forecast cost at completion, projected at the current burn rate.

    In progress it is never below the estimate; at 100% it is the actual; at 0% the estimate.
    """
    estimate = _known(cost_centre.estimated_cost, "estimated_cost")
    actual = _known(cost_centre.actual_cost_to_date, "actual_cost_to_date")
    if percent_complete == HUNDRED:
        return actual
    if percent_complete == ZERO:
        return estimate
    return max(estimate, actual / percent_complete * HUNDRED)


def _cost_centre_result(cost_centre: CostCentre, percent_complete: Decimal) -> CostCentreResult:
    estimate = _known(cost_centre.estimated_cost, "estimated_cost")
    forecast = forecast_at_completion(cost_centre, percent_complete)
    return CostCentreResult(
        name=cost_centre.name,
        estimated_cost=estimate,
        actual_cost_to_date=_known(cost_centre.actual_cost_to_date, "actual_cost_to_date"),
        forecast_at_completion=forecast,
        overrun_dollars=forecast - estimate,
        overrun_pct=None if estimate == ZERO else (forecast / estimate - 1) * HUNDRED,
    )


def compute_metrics(job: Job) -> JobMetrics:
    """Metrics for a job that has passed the NEEDS_REVIEW checks."""
    sell = _known(job.quoted_sell_ex_gst, "quoted_sell_ex_gst")
    percent = _known(job.percent_complete, "percent_complete")
    centres = tuple(_cost_centre_result(c, percent) for c in job.cost_centres)
    estimated_total = sum((c.estimated_cost for c in centres), ZERO)
    forecast_total = sum((c.forecast_at_completion for c in centres), ZERO)
    quoted = (sell - estimated_total) / sell * HUNDRED
    forecast = (sell - forecast_total) / sell * HUNDRED
    return JobMetrics(
        estimated_total=estimated_total,
        forecast_total=forecast_total,
        quoted_margin_pct=quoted,
        forecast_margin_pct=forecast,
        margin_erosion_pts=quoted - forecast,
        dollars_at_risk=max(ZERO, forecast_total - estimated_total),
        cost_centres=centres,
    )


def main_driver(metrics: JobMetrics) -> str | None:
    """Cost centre with the largest overrun in dollars (ties alphabetical), or None."""
    over = [c for c in metrics.cost_centres if c.overrun_dollars > ZERO]
    if not over:
        return None
    return min(over, key=lambda c: (-c.overrun_dollars, c.name)).name


def summarise_portfolio(assessments: Sequence[JobAssessment]) -> PortfolioSummary:
    """Counts and portfolio figures for one run. NEEDS_REVIEW jobs are left out of the money."""
    counts = {status: 0 for status in STATUS_ORDER}
    sell_total = ZERO
    forecast_total = ZERO
    at_risk_total = ZERO
    for assessment in assessments:
        counts[assessment.status] += 1
        metrics = assessment.metrics
        if metrics is None:
            continue
        sell_total += _known(assessment.job.quoted_sell_ex_gst, "quoted_sell_ex_gst")
        forecast_total += metrics.forecast_total
        at_risk_total += metrics.dollars_at_risk
    average = None if sell_total == ZERO else (sell_total - forecast_total) / sell_total * HUNDRED
    return PortfolioSummary(
        counts=counts,
        total_jobs=len(assessments),
        jobs_needing_action=counts[Status.LOSS] + counts[Status.AT_RISK],
        jobs_to_review=counts[Status.NEEDS_REVIEW],
        total_dollars_at_risk=at_risk_total,
        average_forecast_margin_pct=average,
    )
