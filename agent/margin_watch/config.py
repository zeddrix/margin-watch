"""Load thresholds and settings from config/*.toml."""

from __future__ import annotations

from pathlib import Path

from margin_watch.models import Thresholds

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"


class ConfigError(Exception):
    """A config file is missing, unreadable or incomplete."""


def load_thresholds(path: Path | None = None) -> Thresholds:
    """Read `[status]` thresholds; defaults to config/thresholds.toml."""
    raise NotImplementedError
