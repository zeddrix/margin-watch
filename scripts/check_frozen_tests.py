#!/usr/bin/env python3
"""Fail if any test file that existed at a `tests-approved-*` tag was changed, moved or deleted.

Compares each tag with the working tree, so uncommitted edits are caught too. New test files
added after a tag are fine (they belong to a later phase).
"""

import subprocess
import sys

TEST_DIRS = ["agent/tests", "dashboard/tests"]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def main() -> int:
    tags = git("tag", "--list", "tests-approved-*").split()
    if not tags:
        print("No tests-approved-* tags yet.")
        return 0
    problems = []
    for tag in sorted(tags):
        changed = git("diff", "--name-only", "--diff-filter=MDR", tag, "--", *TEST_DIRS).split()
        problems += [f"{tag}: {path}" for path in changed]
        print(f"{tag}: {'OK' if not changed else f'{len(changed)} approved file(s) changed'}")
    if problems:
        print("Approved tests were changed:\n- " + "\n- ".join(problems))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
