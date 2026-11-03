"""Domain types. Money and percentages are Decimal; percentages are in percent units (20 = 20%)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CostCentre(_Frozen):
    """A Simpro-style cost centre on a job. Hours and rate are context only, never used in maths."""

    name: str = Field(min_length=1)
    estimated_cost: Decimal | None
    actual_cost_to_date: Decimal | None
    estimated_hours: Decimal | None = None
    actual_hours: Decimal | None = None
    hourly_rate: Decimal | None = None


class Job(_Frozen):
    """A Simpro-style job. Values may be missing; missing values make the job NEEDS_REVIEW."""

    id: str = Field(min_length=1)
    name: str
    client: str
    site: str
    stage: str
    project_manager: str
    quoted_sell_ex_gst: Decimal | None
    percent_complete: Decimal | None
    cost_centres: tuple[CostCentre, ...]


class Snapshot(_Frozen):
    """One export of jobs, as of a date."""

    snapshot_date: date | None
    jobs: tuple[Job, ...]


class Status(StrEnum):
    LOSS = "LOSS"
    AT_RISK = "AT_RISK"
    WATCH = "WATCH"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ON_TRACK = "ON_TRACK"


STATUS_ORDER: tuple[Status, ...] = (
    Status.LOSS,
    Status.AT_RISK,
    Status.WATCH,
    Status.NEEDS_REVIEW,
    Status.ON_TRACK,
)


class Thresholds(_Frozen):
    at_risk_margin_pct: Decimal
    at_risk_erosion_pts: Decimal
    watch_erosion_pts: Decimal
    watch_overrun_pct: Decimal


class CostCentreResult(_Frozen):
    name: str
    estimated_cost: Decimal
    actual_cost_to_date: Decimal
    forecast_at_completion: Decimal
    overrun_dollars: Decimal
    overrun_pct: Decimal | None


class JobMetrics(_Frozen):
    estimated_total: Decimal
    forecast_total: Decimal
    quoted_margin_pct: Decimal
    forecast_margin_pct: Decimal
    margin_erosion_pts: Decimal
    dollars_at_risk: Decimal
    cost_centres: tuple[CostCentreResult, ...]


class ReviewProblem(_Frozen):
    code: str
    reason: str


class JobAssessment(_Frozen):
    job: Job
    status: Status
    reason: str
    review_code: str | None
    main_driver: str | None
    metrics: JobMetrics | None


class PortfolioSummary(_Frozen):
    counts: dict[Status, int]
    total_jobs: int
    jobs_needing_action: int
    jobs_to_review: int
    total_dollars_at_risk: Decimal
    average_forecast_margin_pct: Decimal | None
