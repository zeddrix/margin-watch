"""`margin-watch serve`: a small local helper for the demo, on 127.0.0.1 only.

It serves the built dashboard, the run files from the output folder, the Excel report and the
email preview, and `POST /api/run`, which streams a live dry run (see live.py) as NDJSON.
Only the offline demo AI can be run from here; nothing is ever sent.
"""

from __future__ import annotations

import json
import mimetypes
import re
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from margin_watch.live import LIVE_AI, SAMPLE_DIR, run_live, sample_dates

HOST = "127.0.0.1"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_RUN_FILE = re.compile(r"^/runs/([\w-]+\.json)$")
# The only output files the browser may fetch: the reports and the email drafts.
_OUTPUT_FILES = (
    re.compile(r"^margin-report-\d{4}-\d{2}-\d{2}\.xlsx$"),
    re.compile(r"^email/preview-\d{4}-\d{2}-\d{2}\.html$"),
    re.compile(r"^email/graph-sendmail-\d{4}-\d{2}-\d{2}\.json$"),
)
_GENERATED = ("runs/*.json", "margin-report-*.xlsx", "email/preview-*.html",
              "email/graph-sendmail-*.json")  # fmt: skip


@dataclass(frozen=True)
class Response:
    status: int
    content_type: str
    body: bytes | Iterator[bytes]


def _json(status: int, value: Any) -> Response:
    return Response(status, "application/json", json.dumps(value).encode())


_NOT_FOUND = Response(404, "text/plain; charset=utf-8", b"Not found")


def _content_type(path: Path) -> str:
    if path.suffix == ".xlsx":
        return XLSX
    guessed = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return (
        f"{guessed}; charset=utf-8" if guessed.startswith(("text/", "application/j")) else guessed
    )


def _inside(root: Path, relative: str) -> Path | None:
    """`root / relative` if it is an existing file inside `root` (no `..` escapes), else None."""
    base = root.resolve()
    target = (base / relative).resolve()
    if base != target and base not in target.parents:
        return None
    return target if target.is_file() else None


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
        self._busy = threading.Lock()

    # --- routing ----------------------------------------------------------------------------

    def handle(self, method: str, path: str, body: bytes = b"") -> Response:
        route = unquote(urlsplit(path).path)
        if ".." in route.split("/"):
            return _NOT_FOUND
        if method == "GET" and route == "/api/health":
            return _json(200, {"live": True, "dry_run": True,
                               "sample_dates": sample_dates(self.sample_dir)})  # fmt: skip
        if method == "POST" and route == "/api/run":
            return self._run(body)
        if method == "POST" and route == "/api/reset":
            return self._reset()
        if method != "GET":
            return _json(405, {"error": "Method not allowed"})
        if route.startswith("/runs/"):
            return self._file(self.output_dir / "runs", _RUN_FILE, route)
        if route.startswith("/files/"):
            relative = route.removeprefix("/files/")
            if not any(p.match(relative) for p in _OUTPUT_FILES):
                return _NOT_FOUND
            found = _inside(self.output_dir, relative)
            return Response(200, _content_type(found), found.read_bytes()) if found else _NOT_FOUND
        return self._static(route)

    def _file(self, root: Path, pattern: re.Pattern[str], route: str) -> Response:
        match = pattern.match(route)
        found = _inside(root, match.group(1)) if match else None
        return Response(200, _content_type(found), found.read_bytes()) if found else _NOT_FOUND

    def _static(self, route: str) -> Response:
        relative = route.lstrip("/") or "index.html"
        found = _inside(self.dashboard_dir, relative)
        if found is None and "." not in Path(relative).name:
            found = _inside(self.dashboard_dir, "index.html")  # client-side routes
        return Response(200, _content_type(found), found.read_bytes()) if found else _NOT_FOUND

    # --- the live run -------------------------------------------------------------------------

    def _run(self, body: bytes) -> Response:
        try:
            request = json.loads(body or b"{}")
        except ValueError:
            return _json(400, {"error": "The request body must be JSON."})
        if not isinstance(request, dict):
            return _json(400, {"error": "The request body must be a JSON object."})
        ai = request.get("ai", "demo")
        dates = sample_dates(self.sample_dir)
        as_of = request.get("as_of") or (dates[-1] if dates else "")
        if ai not in LIVE_AI:
            return _json(400, {"error": "Only the offline demo AI (demo, demo-bad) runs here."})
        if as_of not in dates:
            return _json(400, {"error": f"No sample data for {as_of!r}."})
        if not self._busy.acquire(blocking=False):
            return _json(409, {"error": "A run is already going. Wait for it to finish."})
        return Response(200, "application/x-ndjson; charset=utf-8", self._stream(ai, as_of))

    def _stream(self, ai: str, as_of: str) -> Iterator[bytes]:
        try:
            for event in run_live(
                as_of=as_of,
                ai=ai,
                output_dir=self.output_dir,
                source=self.sample_dir / f"jobs-{as_of}.json",
                pace=self.pace,
                sleep=self.sleep,
            ):
                yield (json.dumps(event, ensure_ascii=False) + "\n").encode()
        finally:
            self._busy.release()

    def _reset(self) -> Response:
        """Delete only generated files (run files, reports, email drafts) from the output folder."""
        for pattern in _GENERATED:
            for path in self.output_dir.glob(pattern):
                path.unlink()
        return Response(204, "text/plain", b"")


class _Handler(BaseHTTPRequestHandler):
    app: LiveApp

    def _respond(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        response = self.app.handle(method, self.path, body)
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", "no-store")
        if isinstance(response.body, bytes):
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            self.wfile.write(response.body)
            return
        # Stream the live run line by line; the connection closes when the run ends.
        self.send_header("Connection", "close")
        self.end_headers()
        for chunk in response.body:
            self.wfile.write(chunk)
            self.wfile.flush()

    def do_GET(self) -> None:
        self._respond("GET")

    def do_POST(self) -> None:
        self._respond("POST")

    def log_message(self, format: str, *args: Any) -> None:  # keep the demo terminal quiet
        return


def make_server(app: LiveApp, port: int) -> ThreadingHTTPServer:
    """An HTTP server for `app`, bound to 127.0.0.1 only."""
    handler = type("LiveHandler", (_Handler,), {"app": app})
    return ThreadingHTTPServer((HOST, port), handler)
