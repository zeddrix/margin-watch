"""Job sources. `SampleFileSource` reads a Simpro-shaped JSON export.

`SimproSource` (documented only, see docs/spec.md) would call the Simpro REST API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from margin_watch.models import Snapshot


class SourceError(Exception):
    """The input is structurally invalid. The message names the file, job id and field."""


class JobSource(Protocol):
    def load(self) -> Snapshot: ...


class SampleFileSource:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Snapshot:
        raise NotImplementedError
