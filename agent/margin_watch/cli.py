"""`margin-watch run`. Exit codes: 0 ok, 2 invalid input file (or usage), 1 unexpected error."""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

import typer
from dotenv import load_dotenv

from margin_watch.config import load_settings, load_thresholds
from margin_watch.formatting import format_date
from margin_watch.labels import summary_label
from margin_watch.models import RunReport, Status, Summary
from margin_watch.run import build_report, write_outputs
from margin_watch.sources import SampleFileSource, SourceError
from margin_watch.summarise import create_summary

AI_CHOICES = ("demo", "demo-bad", "local", "claude", "off")
AGENT_DIR = Path(__file__).resolve().parents[1]

app = typer.Typer(
    add_completion=False,
    help="Morning margin check for HVAC jobs (sample data only; nothing is sent).",
)


@app.callback()
def main() -> None:
    """margin-watch: calculations in code, verified summary, Excel report, Graph email draft."""


def _parse_as_of(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise typer.BadParameter(
            f"{value!r} isn't a date; use YYYY-MM-DD", param_hint="--as-of"
        ) from None


def _parse_generated_at(value: str | None, timezone: str) -> datetime:
    zone = ZoneInfo(timezone)
    if value is None:
        return datetime.now(zone).replace(microsecond=0)
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        raise typer.BadParameter(
            f"{value!r} isn't an ISO 8601 date-time", param_hint="--generated-at"
        ) from None
    return moment if moment.tzinfo else moment.replace(tzinfo=zone)


def _parse_ai(value: str | None) -> str:
    choice = (value or os.environ.get("MARGIN_WATCH_AI") or "demo").strip().lower()
    if choice not in AI_CHOICES:
        raise typer.BadParameter(
            f"{choice!r}; choose one of {', '.join(AI_CHOICES)}", param_hint="--ai"
        )
    return choice


def make_summary(ai: str, report: RunReport) -> Summary | None:
    """The AI summary for `ai`, or None for the template (`off`)."""
    return create_summary(report, ai, os.environ)


def _load_env_file() -> None:
    """Load agent/.env if present, never overriding real env vars.

    `MARGIN_WATCH_ENV_FILE` points elsewhere; an empty value skips it (tests do this).
    """
    path = os.environ.get("MARGIN_WATCH_ENV_FILE", str(AGENT_DIR / ".env"))
    if path and Path(path).is_file():
        load_dotenv(path, override=False)


def _headline(report: RunReport) -> str:
    counts = report.portfolio.counts
    return (
        f"Margin watch run for {format_date(report.as_of)} (sample data): "
        f"{counts[Status.LOSS]} loss, {counts[Status.AT_RISK]} at risk, "
        f"{counts[Status.WATCH]} watch, {counts[Status.NEEDS_REVIEW]} to review, "
        f"{counts[Status.ON_TRACK]} on track."
    )


@app.command()
def run(
    source: Annotated[
        Path | None, typer.Option(help="Job snapshot JSON (default: config/settings.toml).")
    ] = None,
    as_of: Annotated[
        str | None, typer.Option("--as-of", help="Run date, YYYY-MM-DD (default: snapshot date).")
    ] = None,
    ai: Annotated[
        str | None,
        typer.Option(
            help="Summary provider: demo|demo-bad|local|claude|off (env MARGIN_WATCH_AI)."
        ),
    ] = None,
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", help="Where to write outputs (default: output/).")
    ] = None,
    generated_at: Annotated[
        str | None,
        typer.Option(
            "--generated-at", help="Fix the run timestamp (ISO 8601), for reproducible runs."
        ),
    ] = None,
) -> None:
    """Run the morning margin check: Excel report, run JSON and a dry-run email draft."""
    _load_env_file()
    run_date = _parse_as_of(as_of)
    choice = _parse_ai(ai)
    try:
        settings = load_settings()
        moment = _parse_generated_at(generated_at, settings.timezone)
        source_path = source or settings.sample_source
        snapshot = SampleFileSource(source_path).load()
        report = build_report(
            snapshot,
            source_name=source_path.name,
            as_of=run_date or snapshot.snapshot_date or moment.date(),
            generated_at=moment,
            thresholds=load_thresholds(),
        )
        summary = make_summary(choice, report)
        if summary is not None:
            report = report.model_copy(update={"summary": summary})
        outputs = write_outputs(report, output_dir or settings.output_dir, settings.email_to)
    except SourceError as error:
        typer.echo(f"Invalid input file: {error}", err=True)
        raise typer.Exit(2) from None
    except typer.BadParameter:
        raise
    except Exception as error:  # the CLI boundary: report, never show a traceback
        typer.echo(f"Unexpected error: {type(error).__name__}: {error}", err=True)
        raise typer.Exit(1) from None

    typer.echo(_headline(report))
    typer.echo(f"Summary: {summary_label(report.summary)}")
    typer.echo("Wrote:")
    for path in outputs.all():
        typer.echo(f"  {path}")


@app.command()
def serve(
    port: Annotated[int, typer.Option(help="Port on 127.0.0.1.")] = 4173,
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", help="Where runs are written (default: output/).")
    ] = None,
    pace: Annotated[
        float, typer.Option(help="Seconds each step stays on screen, so people can follow it.")
    ] = 0.9,
    dashboard_dir: Annotated[
        Path | None,
        typer.Option("--dashboard-dir", help="Built dashboard (default: dashboard/build)."),
    ] = None,
) -> None:
    """Serve the dashboard with a live "Run this morning's check" button (127.0.0.1 only)."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Placeholder(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_error(501)

        def do_POST(self) -> None:
            self.send_error(501)

    HTTPServer(("127.0.0.1", port), Placeholder).serve_forever()
