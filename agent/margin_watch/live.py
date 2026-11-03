"""The live dry run behind the dashboard's "Run this morning's check" button.

It runs the real pipeline step by step and yields plain-English events for the screen. Every
number in the events is formatted by Python. Nothing is sent; only the offline demo AI is used.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from margin_watch.config import REPO_ROOT

SAMPLE_DIR = REPO_ROOT / "data" / "sample"
LIVE_AI = ("demo", "demo-bad")
STEPS: tuple[tuple[str, str], ...] = (
    ("read", "Reading the jobs"),
    ("maths", "Doing the maths"),
    ("review", "Catching bad data"),
    ("summary", "AI writes the summary, and every number is checked"),
    ("excel", "Saving the Excel report"),
    ("email", "Drafting the morning email"),
    ("dashboard", "Updating the dashboard"),
)


def sample_dates(sample_dir: Path = SAMPLE_DIR) -> list[str]:
    """ISO dates that have a sample file, oldest first."""
    raise NotImplementedError


def run_live(
    *,
    as_of: str,
    ai: str,
    output_dir: Path,
    source: Path | None = None,
    pace: float = 0.9,
    sleep: Callable[[float], None] = time.sleep,
    now: datetime | None = None,
) -> Iterator[dict[str, Any]]:
    """Run the morning check for `as_of`, yielding start, step and done (or error) events."""
    raise NotImplementedError
