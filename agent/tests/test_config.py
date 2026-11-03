"""Thresholds come from config/thresholds.toml (AC-26)."""

from decimal import Decimal

import pytest
from conftest import REPO_ROOT, cc, make_job

from margin_watch.config import ConfigError, load_thresholds
from margin_watch.models import Status
from margin_watch.status import assess_job

CUSTOM = """
[status]
at_risk_margin_pct = 12.0
at_risk_erosion_pts = 8.0
watch_erosion_pts = 3.0
watch_overrun_pct = 15.0
"""


def test_ac26_default_thresholds_file():
    """AC-26: config/thresholds.toml loads as 10 / 8 / 3 / 15, as Decimals."""
    for thresholds in (
        load_thresholds(),
        load_thresholds(REPO_ROOT / "config" / "thresholds.toml"),
    ):
        assert thresholds.at_risk_margin_pct == Decimal("10")
        assert thresholds.at_risk_erosion_pts == Decimal("8")
        assert thresholds.watch_erosion_pts == Decimal("3")
        assert thresholds.watch_overrun_pct == Decimal("15")
        assert isinstance(thresholds.watch_overrun_pct, Decimal)


def test_ac26_custom_threshold_changes_status(tmp_path):
    """AC-26: with at_risk_margin_pct = 12, an 11% forecast margin with no erosion is AT_RISK."""
    path = tmp_path / "thresholds.toml"
    path.write_text(CUSTOM)
    job = make_job([cc("Labour", "89000", "89000")])  # 11% quoted and forecast

    assert assess_job(job, load_thresholds(path)).status == Status.AT_RISK
    assert assess_job(job, load_thresholds()).status == Status.ON_TRACK


def test_ac26_missing_key_names_the_key(tmp_path):
    """AC-26: a thresholds file missing a key raises ConfigError naming that key."""
    path = tmp_path / "thresholds.toml"
    path.write_text(CUSTOM.replace("watch_overrun_pct = 15.0\n", ""))

    with pytest.raises(ConfigError, match="watch_overrun_pct"):
        load_thresholds(path)
