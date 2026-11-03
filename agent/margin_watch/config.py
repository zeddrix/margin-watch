"""Load thresholds and settings from config/*.toml."""

from __future__ import annotations

import tomllib
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from margin_watch.models import Thresholds

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"

_THRESHOLD_KEYS = (
    "at_risk_margin_pct",
    "at_risk_erosion_pts",
    "watch_erosion_pts",
    "watch_overrun_pct",
)


class ConfigError(Exception):
    """A config file is missing, unreadable or incomplete."""


def read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except FileNotFoundError as error:
        raise ConfigError(f"Config file not found: {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"Config file {path} is not valid TOML: {error}") from error


def load_thresholds(path: Path | None = None) -> Thresholds:
    """Read `[status]` thresholds; defaults to config/thresholds.toml."""
    path = path or CONFIG_DIR / "thresholds.toml"
    section = read_toml(path).get("status", {})
    values: dict[str, Decimal] = {}
    for key in _THRESHOLD_KEYS:
        if key not in section:
            raise ConfigError(f"{path.name}: [status] is missing `{key}`")
        try:
            # str() first so a TOML float like 10.0 becomes Decimal("10.0"), not a binary float.
            values[key] = Decimal(str(section[key]))
        except InvalidOperation as error:
            raise ConfigError(f"{path.name}: `{key}` must be a number") from error
    return Thresholds(**values)


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    sample_source: Path
    output_dir: Path
    timezone: str
    email_to: str


def load_settings(path: Path | None = None) -> Settings:
    """Read config/settings.toml. Relative paths resolve against the repo root."""
    path = path or CONFIG_DIR / "settings.toml"
    document = read_toml(path)
    run = document.get("run", {})
    email = document.get("email", {})
    required = {
        "[run] sample_source": run.get("sample_source"),
        "[run] output_dir": run.get("output_dir"),
        "[run] timezone": run.get("timezone"),
        "[email] to": email.get("to"),
    }
    for key, value in required.items():
        if not isinstance(value, str) or not value:
            raise ConfigError(f"{path.name}: `{key}` is missing")
    return Settings(
        sample_source=REPO_ROOT / str(run["sample_source"]),
        output_dir=REPO_ROOT / str(run["output_dir"]),
        timezone=str(run["timezone"]),
        email_to=str(email["to"]),
    )
