#!/usr/bin/env python3
"""Regenerate dashboard/tests/fixtures/ by running the real margin-watch CLI on the sample data.

Committed so the fixture shapes can't drift from what the agent really writes:
- runs/            3 Nov with --ai demo-bad (a rejected AI answer) and 4 Nov with --ai demo
- runs-empty/      an index with no runs
- runs-malformed/  a real index whose 4 Nov run file is truncated JSON (3 Nov stays valid)

Deterministic: fixed --generated-at, and agent/.env is ignored. Usage: python3 scripts/generate_dashboard_fixtures.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "dashboard" / "tests" / "fixtures"
RUNS = (("2026-11-03", "demo-bad"), ("2026-11-04", "demo"))


def run_cli(out_dir: Path, as_of: str, ai: str) -> None:
    command = [
        "uv", "run", "--project", str(ROOT / "agent"), "margin-watch", "run",
        "--source", str(ROOT / "data" / "sample" / f"jobs-{as_of}.json"),
        "--ai", ai,
        "--generated-at", f"{as_of}T06:30:00+11:00",
        "--output-dir", str(out_dir),
    ]  # fmt: skip
    env = os.environ | {"MARGIN_WATCH_ENV_FILE": ""}
    subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        for as_of, ai in RUNS:
            run_cli(out, as_of, ai)
        runs = FIXTURES / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        for name in ("index.json", "2026-11-03.json", "2026-11-04.json"):
            shutil.copyfile(out / "runs" / name, runs / name)

    empty = FIXTURES / "runs-empty"
    empty.mkdir(parents=True, exist_ok=True)
    (empty / "index.json").write_text(json.dumps({"schema_version": 1, "runs": []}, indent=2) + "\n")

    malformed = FIXTURES / "runs-malformed"
    malformed.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURES / "runs" / "index.json", malformed / "index.json")
    shutil.copyfile(FIXTURES / "runs" / "2026-11-03.json", malformed / "2026-11-03.json")
    truncated = (FIXTURES / "runs" / "2026-11-04.json").read_text()[:400]
    (malformed / "2026-11-04.json").write_text(truncated)

    for path in sorted(FIXTURES.rglob("*.json")):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
