"""Display formatting. The only place numbers are rounded (half-up, away from zero)."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

_WHOLE = Decimal("1")
_ONE_DP = Decimal("0.1")


def _round(value: Decimal, step: Decimal) -> Decimal:
    rounded = value.quantize(step, rounding=ROUND_HALF_UP)
    # Never show "-0": a value that rounds to zero loses its sign.
    return rounded.copy_abs() if rounded.is_zero() else rounded


def format_money(value: Decimal) -> str:
    """AUD, whole dollars, half-up: `$12,481`, `-$1,250`."""
    rounded = _round(value, _WHOLE)
    sign = "-" if rounded < 0 else ""
    return f"{sign}${abs(rounded):,.0f}"


def format_pct(value: Decimal) -> str:
    """One decimal, half-up: `6.3%`, `-1.3%`; never `-0.0%`."""
    return f"{_round(value, _ONE_DP):.1f}%"


def format_pts(value: Decimal) -> str:
    """One decimal plus ` pts`: `8.0 pts`."""
    return f"{_round(value, _ONE_DP):.1f} pts"


def format_date(value: date) -> str:
    """`Wed 4 Nov 2026`."""
    return f"{_DAYS[value.weekday()]} {value.day} {_MONTHS[value.month - 1]} {value.year}"


# Explicit names so output never depends on the machine's locale.
_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
