"""Helpers for Phase 4+ tests that drive the real CLI into a temp output dir."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from conftest import SAMPLE_4_NOV
from typer.testing import CliRunner, Result

from margin_watch.cli import app

GENERATED_AT = "2026-11-04T06:30:00+11:00"
GENERATED_AT_DT = datetime(2026, 11, 4, 6, 30, tzinfo=ZoneInfo("Australia/Melbourne"))
SNAPSHOTS = Path(__file__).resolve().parent / "snapshots"


def run_cli(*args: str) -> Result:
    return CliRunner().invoke(app, ["run", *args])


def run_sample(
    out_dir: Path,
    sample: Path = SAMPLE_4_NOV,
    ai: str = "off",
    generated_at: str = GENERATED_AT,
    extra: tuple[str, ...] = (),
) -> Result:
    return run_cli(
        "--source",
        str(sample),
        "--ai",
        ai,
        "--generated-at",
        generated_at,
        "--output-dir",
        str(out_dir),
        *extra,
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot(name: str) -> str:
    return (SNAPSHOTS / name).read_text(encoding="utf-8")
