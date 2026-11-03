"""Shared test helpers: explicit builders, a fixed as-of date and an autouse socket guard."""

from __future__ import annotations

import socket
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from margin_watch.models import CostCentre, Job, Thresholds

AS_OF = date(2026, 11, 4)
REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = REPO_ROOT / "data" / "sample"
SAMPLE_4_NOV = SAMPLE_DIR / "jobs-2026-11-04.json"
SAMPLE_3_NOV = SAMPLE_DIR / "jobs-2026-11-03.json"

# Written out literally so tests don't depend on the config loader.
DEFAULT_THRESHOLDS = Thresholds(
    at_risk_margin_pct=Decimal("10"),
    at_risk_erosion_pts=Decimal("8"),
    watch_erosion_pts=Decimal("3"),
    watch_overrun_pct=Decimal("15"),
)


def _dec(value: str | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def cc(name: str = "Labour", est: str | None = "10000", act: str | None = "0") -> CostCentre:
    """A cost centre with an estimate and an actual cost to date (strings, or None for missing)."""
    return CostCentre(name=name, estimated_cost=_dec(est), actual_cost_to_date=_dec(act))


def make_job(
    cost_centres: Sequence[CostCentre] = (),
    *,
    job_id: str = "T1",
    sell: str | None = "100000",
    percent_complete: str | None = "100",
    name: str = "Test job",
    client: str = "Test client",
    site: str = "Test site",
    pm: str = "Test PM",
) -> Job:
    """A job. Defaults: sell $100,000 and 100% complete, so forecast = actual."""
    return Job(
        id=job_id,
        name=name,
        client=client,
        site=site,
        stage="In progress",
        project_manager=pm,
        quoted_sell_ex_gst=_dec(sell),
        percent_complete=_dec(percent_complete),
        cost_centres=tuple(cost_centres),
    )


@pytest.fixture(autouse=True)
def _socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail any test that tries to open a network connection or resolve a host."""

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("Network access is blocked in tests (socket guard).")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
