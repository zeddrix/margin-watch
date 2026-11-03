#!/usr/bin/env python3
"""Fail on banned test patterns and on AC <-> test traceability gaps."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BANNED = [
    r"pytest\.mark\.skip", r"pytest\.mark\.xfail", r"pytest\.skip\(",
    r"\btest\.skip\b", r"\btest\.only\b", r"\btest\.fixme\b",
    r"\bit\.only\b", r"\bdescribe\.only\b", r"assert True\b", r"expect\(true\)",
]
problems: list[str] = []

test_files = [
    p for p in ROOT.glob("**/*")
    if p.is_file() and "node_modules" not in p.parts and ".venv" not in p.parts
    and (re.match(r"test_.*\.py$", p.name) or re.search(r"\.(test|spec)\.ts$", p.name))
]
cited: set[str] = set()
for path in test_files:
    text = path.read_text()
    for pattern in BANNED:
        if re.search(pattern, text):
            problems.append(f"{path.relative_to(ROOT)}: banned pattern {pattern}")
    for name_line in re.findall(r"(?:def (test_\w+)|\b(?:test|it)\(\s*['\"`]([^'\"`]+))", text):
        name = name_line[0] or name_line[1]
        ids = re.findall(r"ac[-_]?(\d{2,3})", name, re.I)
        if not ids and name != "test_smoke":
            problems.append(f"{path.relative_to(ROOT)}: test '{name}' has no AC ID")
        cited.update(f"AC-{i.zfill(2)}" for i in ids)

ac_file = ROOT / "docs" / "acceptance-criteria.md"
if ac_file.exists():
    defined = set(re.findall(r"\bAC-\d{2,3}\b", ac_file.read_text()))
    for ac in sorted(defined - cited):
        problems.append(f"{ac} has no test")

pw_config = ROOT / "dashboard" / "playwright.config.ts"
if pw_config.exists() and re.search(r"retries:\s*[1-9]", pw_config.read_text()):
    problems.append("playwright.config.ts: retries must be 0")

if problems:
    print("Test integrity check FAILED:\n- " + "\n- ".join(problems))
    sys.exit(1)
print(f"Test integrity OK ({len(test_files)} test files, {len(cited)} ACs covered)")
