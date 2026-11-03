"""Display formatting. The only place numbers are rounded (half-up)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal


def format_money(value: Decimal) -> str:
    """AUD, whole dollars, half-up: `$12,481`, `-$1,250`."""
    raise NotImplementedError


def format_pct(value: Decimal) -> str:
    """One decimal, half-up: `6.3%`, `-1.3%`; never `-0.0%`."""
    raise NotImplementedError


def format_pts(value: Decimal) -> str:
    """One decimal plus ` pts`: `8.0 pts`."""
    raise NotImplementedError


def format_date(value: date) -> str:
    """`Wed 4 Nov 2026`."""
    raise NotImplementedError
