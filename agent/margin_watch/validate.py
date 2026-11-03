"""Number verification: every number in the model's text must match a number in the facts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    rejected: tuple[str, ...]


def extract_tokens(text: str) -> list[str]:
    """Number tokens (money, %, pts, decimals, integers) in their canonical form."""
    raise NotImplementedError


def allowed_tokens(facts: Any) -> frozenset[str]:
    """Every number token found in any string value of the facts."""
    raise NotImplementedError


def validate_text(text: str, allowed: frozenset[str]) -> ValidationResult:
    raise NotImplementedError
