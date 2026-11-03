# Progress

| Phase | Status | Tests | Commit | Notes |
|---|---|---|---|---|
| 0. Setup | done | n/a | 97ea5af | git 2.50.1, uv 0.10.7, node v25.8.1, npm 11.11.0, system python3 3.9.6; Python 3.12.12 installed with `uv python install 3.12`. Hook check: a `Write` to `.claude/allow-test-edits` was **blocked** ("BLOCKED: only Zeddrix changes the test guardrails."). Shell commands that merely mention that filename are blocked too. |
| 1. Plan | done | n/a | b8cddaa | `docs/spec.md` (formulas, rules, hand-calculated tables for both dates), Phase 2 ACs AC-01..AC-33, later phases as bullets, 14 fictional jobs × 2 dates, decisions 1–15. |
| 2. Calculation tests (red) | done | 91 red + 1 smoke | tag `tests-approved-2` | Red run: `91 failed, 1 passed`; all 91 failures are `NotImplementedError` (no import/fixture errors). Integrity: 7 test files, 33 ACs covered. Self-review done (see below). |
| 3. Calculations (green) | done | 92 passed (91 AC + smoke) | see `git log` (feat: margin calculations…) | ruff, ruff format, mypy --strict clean. Coverage 95.8% package; calc.py and status.py 100% (branch). Integrity OK (33 ACs). Diff vs `tests-approved-2` on the test dirs is empty. |
| 4a. Outputs & CLI tests (red) | done | 33 red + 92 green | tag `tests-approved-4` | AC-34..AC-51 written first. Red run: `33 failed, 92 passed`; every failure is `NotImplementedError` (raised directly, or the CLI stub exiting 1 with `Result NotImplementedError()`). Snapshots `email-2026-11-04.html` and `template-summary-2026-11-04.txt` hand-written and reviewed line by line. Integrity: 12 test files, 51 ACs. |

## Phase 2 self-review notes

- Boundaries below / at / above for 0% (LOSS), 10% margin, 8 pts, 3 pts, 15% overrun, 100% complete.
- Mutation examples: `<=` instead of `<` on the 10% floor fails AC-10 at 90,000; `>` instead of `≥` on erosion fails AC-11/12 at exactly 8 / 3 pts; dropping `max(estimate, burn-rate)` fails AC-03; banker's rounding fails AC-33 (6.25, 12,480.50); driver by percent fails AC-23; simple-mean average fails AC-31; float JSON parsing fails AC-27; wrong NEEDS_REVIEW order fails AC-22.
- Lint fixes made before locking: long docstrings wrapped, `O` renamed `OK`, regex-escaped `match=` patterns, fixture `yield` → `return`.
