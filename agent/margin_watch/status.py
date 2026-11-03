"""Job status rules. See docs/spec.md, "Status rules"."""

from __future__ import annotations

from collections.abc import Sequence

from margin_watch.models import Job, JobAssessment, ReviewProblem, Thresholds


def review_problem(job: Job) -> ReviewProblem | None:
    """The first data problem that makes a job NEEDS_REVIEW, or None."""
    raise NotImplementedError


def assess_job(job: Job, thresholds: Thresholds) -> JobAssessment:
    """Status, reason, main driver and metrics for one job."""
    raise NotImplementedError


def sort_assessments(assessments: Sequence[JobAssessment]) -> list[JobAssessment]:
    """Risk order: status, then dollars at risk descending, then job id."""
    raise NotImplementedError


def assess_jobs(jobs: Sequence[Job], thresholds: Thresholds) -> list[JobAssessment]:
    """Assess every job and return them in risk order."""
    raise NotImplementedError
