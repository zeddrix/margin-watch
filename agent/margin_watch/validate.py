"""Number verification: every number in the model's text must match a number in the facts.

A number token is money (`$12,000`, `-$1,250`), a percentage (`6.2%`), points (`20.0 pts`), a
decimal or an integer, with an optional `k` / `m` / `bn` suffix. Tokens are compared in a
canonical form that only removes spelling noise: a space before the unit, "points"/"pt" for
"pts", "percent" for "%", and a Unicode minus for "-". The digits must match exactly, so a
re-rounded figure ("6%" for "6.2%") is rejected.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

_NUMBER = re.compile(
    r"(?<![\w.,$])"  # not the tail of a word or of another number ("Q4", "1.5.2")
    r"(?P<sign>-)?"
    r"(?P<dollar>\$)?"
    r"(?P<digits>\d+(?:,\d{3})*(?:\.\d+)?)"
    r"(?:(?P<space>\s?)(?P<unit>%|percent\b|pts\b|pt\b|points?\b)|(?P<suffix>k|m|bn)\b)?"
    r"(?!\w)",
    re.IGNORECASE,
)
_UNICODE_MINUS = chr(0x2212)
_NO_BREAK_SPACE = chr(0x00A0)
_UNITS = {"%": "%", "percent": "%", "pts": "pts", "pt": "pts", "point": "pts", "points": "pts"}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    rejected: tuple[str, ...]


def _normalise(text: str) -> str:
    return text.replace(_UNICODE_MINUS, "-").replace(_NO_BREAK_SPACE, " ")


def _tokens(text: str) -> Iterator[tuple[str, str]]:
    """(canonical, as written) for each number token in `text`."""
    for match in _NUMBER.finditer(_normalise(text)):
        unit = match["unit"]
        canonical = (
            (match["sign"] or "")
            + (match["dollar"] or "")
            + match["digits"]
            + (_UNITS[unit.lower()] if unit else "")
            + (match["suffix"] or "").lower()
        )
        yield canonical, match.group(0)


def extract_tokens(text: str) -> list[str]:
    """Number tokens (money, %, pts, decimals, integers) in their canonical form."""
    return [canonical for canonical, _ in _tokens(text)]


def _strings(value: Any) -> Iterator[str]:
    """Every string inside nested dicts / lists. Non-string leaves are skipped."""
    if isinstance(value, str):
        yield value
        return
    children = value.values() if isinstance(value, dict) else value
    for item in children if isinstance(value, dict | list | tuple) else ():
        yield from _strings(item)


def allowed_tokens(facts: Any) -> frozenset[str]:
    """Every number token found in any string value of the facts."""
    return frozenset(token for text in _strings(facts) for token in extract_tokens(text))


@dataclass(frozen=True)
class NumberCheck:
    """One number from the text, as written, and whether it matches a calculated fact."""

    token: str
    ok: bool


def check_numbers(text: str, allowed: frozenset[str]) -> list[NumberCheck]:
    """Every distinct number in `text`, in order of appearance, checked against `allowed`."""
    checks: list[NumberCheck] = []
    seen: set[str] = set()
    for canonical, written in _tokens(text):
        if canonical not in seen:
            seen.add(canonical)
            checks.append(NumberCheck(token=written, ok=canonical in allowed))
    return checks


def validate_text(text: str, allowed: frozenset[str]) -> ValidationResult:
    """Reject the text if any number in it isn't in `allowed`. Rejected tokens are listed once."""
    rejected = tuple(c.token for c in check_numbers(text, allowed) if not c.ok)
    return ValidationResult(ok=not rejected, rejected=rejected)
