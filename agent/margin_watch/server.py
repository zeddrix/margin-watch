"""`margin-watch serve`: a small local helper for the demo, on 127.0.0.1 only.

It serves the built dashboard, the run files from the output folder, the Excel report and the
email preview, and `POST /api/run`, which streams a live dry run (see live.py) as NDJSON.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from pathlib import Path

from margin_watch.live import SAMPLE_DIR

HOST = "127.0.0.1"


@dataclass(frozen=True)
class Response:
    status: int
    content_type: str
    body: bytes | Iterator[bytes]


class LiveApp:
    def __init__(
        self,
        *,
        dashboard_dir: Path,
        output_dir: Path,
        pace: float = 0.9,
        sleep: Callable[[float], None] = time.sleep,
        sample_dir: Path = SAMPLE_DIR,
    ) -> None:
        self.dashboard_dir = dashboard_dir
        self.output_dir = output_dir
        self.pace = pace
        self.sleep = sleep
        self.sample_dir = sample_dir

    def handle(self, method: str, path: str, body: bytes = b"") -> Response:
        raise NotImplementedError


def make_server(app: LiveApp, port: int) -> ThreadingHTTPServer:
    """An HTTP server for `app`, bound to 127.0.0.1 only."""
    raise NotImplementedError
