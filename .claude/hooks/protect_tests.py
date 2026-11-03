#!/usr/bin/env python3
"""Block changes to approved (git-tracked) test files and to the guardrails themselves.

New, uncommitted test files can be edited freely (red phase, before the gate).
Once a test file is committed after a gate, it is frozen. Zeddrix can unlock
temporarily with `touch .claude/allow-test-edits`.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
OVERRIDE = os.path.join(ROOT, ".claude", "allow-test-edits")

TEST_PATH = re.compile(
    r"(^|/)(agent/tests|dashboard/tests)/"
    r"|(^|/)test_[^/]*\.py$"
    r"|\.(test|spec)\.ts$"
    r"|(^|/)tests/(fixtures|snapshots)/"
)
GUARDRAILS = re.compile(r"(\.claude/hooks/|\.claude/settings(\.local)?\.json|allow-test-edits|scripts/check_test_integrity\.py)")
# Shell patterns that write, move or delete. `2>&1` is not a write.
WRITES = re.compile(
    r"(^|[^0-9&>])>{1,2}\s*[^&\s]"
    r"|\bsed\s+-i|\bperl\s+-i|\btee\b|\brm\b|\bmv\b|\bcp\b|\btruncate\b"
    r"|\bgit\s+(checkout|restore|rm|mv|reset|stash)\b"
)
TEST_IN_CMD = re.compile(r"(agent/tests|dashboard/tests|test_\w+\.py|\.(test|spec)\.ts|tests/(fixtures|snapshots))")


def block(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def is_tracked(path: str) -> bool:
    absolute = os.path.abspath(os.path.join(ROOT, path))
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", os.path.relpath(absolute, ROOT)],
        cwd=ROOT,
        capture_output=True,
    )
    return result.returncode == 0


def main() -> None:
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    unlocked = os.path.exists(OVERRIDE)

    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if GUARDRAILS.search(path):
            block("BLOCKED: only Zeddrix changes the test guardrails.")
        if TEST_PATH.search(path) and is_tracked(path) and not unlocked:
            block(
                f"BLOCKED: {path} is an approved test (committed after a gate). "
                "Do not change tests to make them pass. Fix the production code, "
                "or stop and ask Zeddrix to approve a test change (docs/testing-rules.md)."
            )
    elif tool == "Bash":
        command = tool_input.get("command", "")
        if "allow-test-edits" in command or (GUARDRAILS.search(command) and WRITES.search(command)):
            block("BLOCKED: only Zeddrix changes the test guardrails.")
        if TEST_IN_CMD.search(command) and WRITES.search(command) and not unlocked:
            block(
                "BLOCKED: this shell command looks like it writes, moves or deletes test files. "
                "Use Edit/Write for new red-phase tests; approved tests are frozen."
            )
    sys.exit(0)


main()
