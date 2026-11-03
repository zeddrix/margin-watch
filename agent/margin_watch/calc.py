"""Pure margin calculations. See docs/spec.md, "Formulas"."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from margin_watch.models import CostCentre, Job, JobAssessment, JobMetrics, PortfolioSummary


def forecast_at_completion(cost_centre: CostCentre, percent_complete: Decimal) -> Decimal:
    """Forecast cost at completion, projected at the current burn rate."""
    raise NotImplementedError


def compute_metrics(job: Job) -> JobMetrics:
    """Metrics for a job that has passed the NEEDS_REVIEW checks."""
    raise NotImplementedError


def main_driver(metrics: JobMetrics) -> str | None:
    """Cost centre with the largest overrun in dollars (ties alphabetical), or None."""
    raise NotImplementedError


def summarise_portfolio(assessments: Sequence[JobAssessment]) -> PortfolioSummary:
    """Counts and portfolio figures for one run."""
    raise NotImplementedError
