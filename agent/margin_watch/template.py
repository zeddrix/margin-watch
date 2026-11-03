"""The template summary: plain wording built by code. Used with --ai off and on every fallback."""

from __future__ import annotations

from collections.abc import Sequence

from margin_watch.models import JobAssessment, PortfolioSummary


def template_summary(assessments: Sequence[JobAssessment], portfolio: PortfolioSummary) -> str:
    """Overview, one paragraph per LOSS / AT_RISK job, then WATCH and NEEDS_REVIEW jobs."""
    raise NotImplementedError
