"""Display formatting, half-up (AC-33)."""

from datetime import date
from decimal import Decimal

import pytest

from margin_watch.formatting import format_date, format_money, format_pct, format_pts


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("12480.50", "$12,481"),
        ("12480.49", "$12,480"),
        ("-1250", "-$1,250"),
        ("0", "$0"),
        ("1234567.5", "$1,234,568"),
        ("999.5", "$1,000"),
    ],
)
def test_ac33_money(value, expected):
    """AC-33: AUD whole dollars, half-up, thousands separators, minus before the $."""
    assert format_money(Decimal(value)) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("6.25", "6.3%"),
        ("-1.25", "-1.3%"),
        ("-0.04", "0.0%"),
        ("15", "15.0%"),
        ("15.7394084", "15.7%"),
        ("-2.5", "-2.5%"),
    ],
)
def test_ac33_percent(value, expected):
    """AC-33: one decimal, half-up away from zero, never -0.0%."""
    assert format_pct(Decimal(value)) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("8", "8.0 pts"), ("18.75", "18.8 pts"), ("-2", "-2.0 pts"), ("-0.01", "0.0 pts")],
)
def test_ac33_points(value, expected):
    """AC-33: one decimal plus ' pts'."""
    assert format_pts(Decimal(value)) == expected


def test_ac33_date():
    """AC-33: 2026-11-04 -> 'Wed 4 Nov 2026' (no leading zero)."""
    assert format_date(date(2026, 11, 4)) == "Wed 4 Nov 2026"
    assert format_date(date(2026, 11, 3)) == "Tue 3 Nov 2026"
