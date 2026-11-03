# Decisions (decision · why · alternative considered)

## Product principles (Phase 1)

1. **The AI never does maths.** Python computes every number and hands the model pre-formatted strings; a validator rejects any number in the model's text that isn't in the facts, and the template is used instead. · Language models misread, re-round and invent figures, and a wrong dollar figure in an ops email costs trust (and money) fast. Keeping maths in tested code makes every number auditable. · Alternative: let the model compute and "check its work". Rejected because it can't be tested deterministically.
2. **The default AI provider is a scripted demo model.** · The demo must run offline, for free and deterministically, while still going through the real tool-use loop, validator and fallback. `demo-bad` shows a rejection on demand. It is always labelled "Demo AI", never Claude. · Alternative: default to Claude. Rejected because it needs a paid key and a network, and the output would vary between runs.
3. **Mail is dry-run only.** `DryRunMailer` writes the exact Graph `sendMail` body plus an HTML preview. · Nothing should ever reach a real inbox from a prototype on fictional data, and the payload file proves the integration shape. · Alternative: send through a test mailbox. Rejected: needs credentials and an external service.
4. **The dashboard reads static run files.** · No backend and no database means nothing to host or secure, the dashboard shows exactly what the agent produced, and E2E tests can use committed fixtures. · Alternative: a small API server. Rejected as unnecessary for one-day scope.

## Calculation details (Phase 1)

5. **Percentages are stored in percent units** (20 means 20%) and erosion is `quoted − forecast` in points. · Same maths as the plan's fraction form ×100, and it reads naturally in JSON and tests. · Alternative: fractions everywhere, converting at display time.
6. **Display money is whole dollars, rounded half-up; files keep cents.** · Matches the plan's example facts ("$12,480") and is what an ops manager scans; Excel and JSON keep exact cents. · Alternative: always show cents (noisier).
7. **NEEDS_REVIEW check order: cost centres → sell → costs → percent complete (missing, out of range, 0% with spend).** · The 0% rule sums actual costs, so costs must already be known and non-negative. The plan's list order wasn't stated as an evaluation order. · Alternative: the plan's listing order.
8. **NEEDS_REVIEW jobs get no metrics at all**, even ones that could be computed (e.g. quoted margin when only percent complete is missing). · Simplest way to guarantee nothing is guessed or half-shown. · Alternative: partial metrics.
9. **Missing sell or missing costs are NEEDS_REVIEW, not file errors** (`missing_sell`, `missing_cost`). Structural problems (bad JSON, missing names, bad types, duplicate ids) are file errors (exit 2). Percent complete below 0 is treated like above 100 (`percent_out_of_range`). · One incomplete job shouldn't stop the whole morning run. · Alternative: fail the run.
10. **Main driver only for LOSS / AT_RISK / WATCH, and only if some overrun is above $0.** · An AT_RISK job can be thin from the quote with nothing over budget. · Alternative: always name the largest line.
11. **Overrun % is null when the estimate is $0** and doesn't count for the 15% rule; its dollars still count in the forecast. · Division by zero has no honest answer. · Alternative: treat as infinite overrun.
12. **"Jobs needing action" = LOSS + AT_RISK.** "Jobs to review" = NEEDS_REVIEW. · These are the phone calls today; WATCH is a heads-up. · Alternative: include WATCH.
13. **Average forecast margin is sell-weighted** across jobs that aren't NEEDS_REVIEW. · A $250k job matters more than a $25k one; this is the portfolio's real margin. · Alternative: simple mean.
14. **`--as-of` defaults to the file's `snapshot_date`.** · Keeps runs deterministic and never reads the clock for business logic. · Alternative: today's date.
15. **Job ids are Simpro-style numbers ("1042").** · Realistic, and it exercises the rule that identifiers in facts don't trip the validator.

## Implementation (Phase 3)

16. **`compute_metrics` states its precondition with `assert`** (every value is known because `review_problem` ran first) instead of a `raise` branch that no caller can reach. · Keeps calc.py at a true 100% coverage without `# pragma: no cover` exclusions; under `python -O` a missing value would still fail loudly in the arithmetic (TypeError), never be defaulted. · Alternative: a raise plus a coverage exclusion (rejected as greenwashing the coverage target).
17. **Coverage is enforced on every pytest run** (`--cov-fail-under=90` in `pyproject.toml`), and `make test` / CI also run `coverage report --include=calc.py,status.py,validate.py --fail-under=100`. · The completion gate then can't pass with low coverage. · Alternative: report-only coverage.
18. **Dates are formatted with explicit English day/month names**, not `strftime("%a")`. · Output must not depend on the machine's locale.
