"""The Excel report: Summary, Jobs and Cost centres sheets (openpyxl)."""

from __future__ import annotations

from pathlib import Path

from margin_watch.models import RunReport


def write_excel(report: RunReport, path: Path) -> Path:
    raise NotImplementedError
