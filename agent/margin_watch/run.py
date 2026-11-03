"""One morning run: load, assess, summarise, write the run JSON, Excel and email draft."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from margin_watch.models import RunReport, Snapshot, Summary, Thresholds


@dataclass(frozen=True)
class RunOutputs:
    run_json: Path
    index_json: Path
    excel: Path
    graph_json: Path
    preview_html: Path


def build_report(
    snapshot: Snapshot,
    *,
    source_name: str,
    as_of: date,
    generated_at: datetime,
    thresholds: Thresholds,
    summary: Summary | None = None,
) -> RunReport:
    """Assess every job. Without a summary, the template summary is used (`--ai off`)."""
    raise NotImplementedError


def report_to_json(report: RunReport) -> dict[str, Any]:
    """The run JSON document (schema version 1)."""
    raise NotImplementedError


def write_outputs(report: RunReport, output_dir: Path, recipient: str) -> RunOutputs:
    """Write the run JSON, update the index, write the Excel report and the email draft."""
    raise NotImplementedError
