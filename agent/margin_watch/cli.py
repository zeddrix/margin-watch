"""`margin-watch run`. Exit codes: 0 ok, 2 invalid input file, 1 unexpected error."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(add_completion=False, help="Morning margin check for HVAC jobs (sample data).")


@app.callback()
def main() -> None:
    """margin-watch: calculations in code, verified summary, Excel report, Graph email draft."""


@app.command()
def run(
    source: Annotated[Path | None, typer.Option(help="Job snapshot JSON.")] = None,
    as_of: Annotated[str | None, typer.Option("--as-of", help="YYYY-MM-DD.")] = None,
    ai: Annotated[str | None, typer.Option(help="demo|demo-bad|local|claude|off")] = None,
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    generated_at: Annotated[str | None, typer.Option("--generated-at")] = None,
) -> None:
    """Run the morning margin check."""
    raise NotImplementedError
