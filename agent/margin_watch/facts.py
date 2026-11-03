"""The facts object: every number pre-formatted as a string by Python, for the model to quote."""

from __future__ import annotations

from typing import Any

from margin_watch.models import RunReport


def build_facts(report: RunReport) -> dict[str, Any]:
    """`{"overview": {...}, "jobs": {job_id: {...}}}` for every job that isn't ON_TRACK."""
    raise NotImplementedError
