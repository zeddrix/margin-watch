"""Job sources. `SampleFileSource` reads a Simpro-shaped JSON export.

`SimproSource` (documented only, see docs/spec.md) would call the Simpro REST API.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from margin_watch.models import Job, Snapshot


class SourceError(Exception):
    """The input is structurally invalid. The message names the file, job id and field."""


class JobSource(Protocol):
    def load(self) -> Snapshot: ...


def _field_path(location: tuple[int | str, ...]) -> str:
    parts: list[str] = []
    for part in location:
        if isinstance(part, int):
            parts[-1] = f"{parts[-1]}[{part}]" if parts else f"[{part}]"
        else:
            parts.append(part)
    return ".".join(parts)


class SampleFileSource:
    """Reads `{"snapshot_date": ..., "jobs": [...]}`. Money is parsed straight to Decimal."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Snapshot:
        name = self.path.name
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise SourceError(f"{name}: file not found ({self.path})") from error
        except OSError as error:
            raise SourceError(f"{name}: can't read the file ({error})") from error
        try:
            # parse_float=Decimal keeps 0.1 as exactly Decimal("0.1"), never a binary float.
            document = json.loads(text, parse_float=Decimal)
        except json.JSONDecodeError as error:
            raise SourceError(
                f"{name}: not valid JSON (line {error.lineno}, column {error.colno})"
            ) from error

        if not isinstance(document, dict):
            raise SourceError(f"{name}: expected a JSON object with a `jobs` list")
        raw_jobs = document.get("jobs")
        if not isinstance(raw_jobs, list):
            raise SourceError(f"{name}: field `jobs` is missing or isn't a list")

        jobs = tuple(self._parse_job(raw, index) for index, raw in enumerate(raw_jobs))
        seen: set[str] = set()
        for job in jobs:
            if job.id in seen:
                raise SourceError(f"{name}: duplicate job id {job.id}")
            seen.add(job.id)
        return Snapshot(snapshot_date=self._snapshot_date(document), jobs=jobs)

    def _snapshot_date(self, document: dict[str, Any]) -> date | None:
        value = document.get("snapshot_date")
        if value is None:
            return None
        try:
            return date.fromisoformat(str(value))
        except ValueError as error:
            raise SourceError(
                f"{self.path.name}: field `snapshot_date` must be YYYY-MM-DD, got {value!r}"
            ) from error

    def _parse_job(self, raw: object, index: int) -> Job:
        if not isinstance(raw, dict):
            raise SourceError(f"{self.path.name}: job #{index + 1} isn't a JSON object")
        label = f"job {raw['id']}" if isinstance(raw.get("id"), str) else f"job #{index + 1}"
        try:
            return Job.model_validate(raw)
        except ValidationError as error:
            first = error.errors()[0]
            field = _field_path(tuple(first["loc"]))
            raise SourceError(
                f"{self.path.name}: {label}: field `{field}`: {first['msg']}"
            ) from error
