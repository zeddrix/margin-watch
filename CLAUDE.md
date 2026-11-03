# margin-watch

One-day prototype for a commercial HVAC / mechanical services contractor in Melbourne. It reads job costing data, calculates margin per job, flags jobs losing margin, writes an Excel report, drafts the ops manager's morning email (a Microsoft Graph sendMail body, dry run), writes a short AI summary whose numbers are verified, and shows it all on a dashboard.

All data is fictional. Sources are *shaped like* Simpro and Microsoft Graph; nothing connects to real systems. No paid API is used: the default AI provider is a built-in scripted demo model.

- `OVERVIEW.md` is Zeddrix's plain-English description of the product. Keep the product consistent with it, and don't edit it.
- `BUILD-PLAN.md` is the plan. Follow it phase by phase, autonomously, until the Final phase is done.
- `docs/acceptance-criteria.md` is the contract.
- `docs/testing-rules.md` is mandatory for every test.

## Working autonomously

- Don't stop to ask questions. Make the most reasonable decision, record it in `docs/decisions.md` (one short entry: decision, why, alternative), and keep going.
- If something truly blocks you (a missing tool you can't install with allowed commands, or an approved test you believe is wrong), write it in `docs/open-questions.md` with what you tried, then continue with every other part of the plan.
- Never push. Never use paid APIs. Never send email or call external services. Never touch other repos or Docker containers.
- Keep `docs/progress.md` updated at the end of each phase: phase, status, test counts, commit hash, notes. If the session restarts, resume from it and `git log`.

## Non-negotiable rules

1. **The AI never does maths.** Every number (money, %, points, hours, counts) is computed by Python. Any model, whether demo, local or Claude, only writes sentences around numbers it was given as pre-formatted strings. A validator rejects AI text containing any number that isn't in the facts, and the template summary is used instead.
2. **ATDD, red → green.** Order: acceptance criteria → failing tests that cite AC IDs → real red run → self-review (BUILD-PLAN.md checklist) → commit + tag → implementation.
3. **Approved tests are frozen.** After the tests of a phase are committed and tagged, never edit, delete, skip, xfail, loosen or rename them, and never change their fixtures or snapshots to make them pass. A hook enforces this. If one seems wrong, log it in `docs/open-questions.md`, fix the production code if the test is right after all, and otherwise continue with other work.
4. **Never greenwash.** No special-casing test inputs in production code, no catch-and-ignore to pass a test, no lowered thresholds or coverage targets. Fix the real behaviour.
5. **Missing data is never guessed.** Bad or incomplete job data gets status NEEDS_REVIEW with a specific reason.
6. **Read-only and dry-run by default.** Nothing is sent. No network calls in Python tests (socket guard). Model clients are injected and faked in tests.
7. **Money is Decimal**, AUD, rounded half-up to cents only when formatting. Percentages are Decimal too.
8. **Deterministic runs:** every run takes an `as_of` date. Tests never read the real clock.
9. Python: type hints everywhere, `ruff` and `mypy --strict` clean. TypeScript: strict, no `any`, no eslint-disable comments, `svelte-check` 0 errors and 0 warnings, eslint `--max-warnings 0`.
10. Docs change in the same commit as the behaviour they describe.
11. Commit at the end of each step the plan names, with a clear message. Tag each approved test commit `tests-approved-<phase>`.

## Completion gate (end of every phase, foreground, no partial runs)

- `cd agent && uv run ruff check . && uv run ruff format --check . && uv run mypy --strict margin_watch && uv run pytest -q`
- `python3 scripts/check_test_integrity.py`
- once the dashboard exists: `cd dashboard && npm run check && npm run lint && npm run test && npm run test:e2e`
- for every tag `tests-approved-*`: `git diff --stat <tag> -- agent/tests dashboard/tests` shows no changes to files that existed at that tag.

Zero failures and zero warnings. There's no such thing as a "pre-existing" failure: anything red in a run you executed gets fixed before the phase is done.

## Layout

- `agent/` Python package `margin_watch`; tests in `agent/tests/`
- `dashboard/` SvelteKit app; tests in `dashboard/tests/` (unit and e2e)
- `config/` thresholds and settings (TOML)
- `data/sample/` fictional jobs
- `prompts/` model system prompts (reviewable text)
- `output/` generated files (git-ignored)
- `docs/` spec, acceptance criteria, testing rules, decisions, progress, scheduling, manual QA, Loom script

## Guardrail files (don't modify)

`.claude/settings.json`, `.claude/hooks/protect_tests.py`, `scripts/check_test_integrity.py`. Only Zeddrix changes these. He can temporarily unlock approved tests with `touch .claude/allow-test-edits`.
