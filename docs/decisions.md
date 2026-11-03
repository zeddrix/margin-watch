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

## Outputs and CLI (Phase 4)

19. **Run JSON carries numbers, not strings** (money to cents, percentages and points to 4 dp, `-0.0` normalised to `0.0`). · The dashboard can sort and compare without parsing; Python stays the source of truth for every figure. · Alternative: Decimal strings (exact but awkward in the browser).
20. **`--generated-at` and `--output-dir` CLI options.** · Fixture generation, `make demo` and tests need reproducible timestamps and an isolated output folder; business logic still never reads the clock (as-of comes from the file). `make demo` passes `<as_of>T06:30:00+11:00` to simulate the scheduled 6:30 AM run. · Alternative: env vars.
21. **`--ai off` records `fallback_reason: "ai_off"`.** · Every template summary then says why it is a template. · Alternative: null.
22. **The run index is updated in place** (replace the entry for the same as-of, sort newest first) rather than rebuilt by scanning `runs/`. · One stray file in the folder can't break the morning run. · Alternative: rebuild from every run file.
23. **Subject line counts LOSS, AT_RISK and NEEDS_REVIEW** (the plan's example); WATCH only appears when nothing else does, and "all N jobs on track" when nothing is flagged.
24. **Template summary leads with "Call {PM} about {id} {name}."** for each LOSS and AT_RISK job, then lists WATCH and NEEDS_REVIEW jobs with their PMs. · The ops manager's first question is who to phone.
25. **Excel stores percentages as fractions with a `0.0%` format** and keeps money to cents with `"$"#,##0.00`. Workbook created/modified timestamps are set to the run's `generated_at`. · Native Excel behaviour; the values stay sortable and summable. Zip entry times inside .xlsx still vary, so determinism is checked on cell values.
26. **A usage error (bad `--as-of`, unknown `--ai`) exits 2**, like an invalid file, using the CLI framework's standard usage message.

## Summary and providers (Phase 5)

27. **Claude request: no `temperature`, `thinking: {"type": "between_tools"}`, `max_tokens` 500.** · The plan says `temperature 0`, but Claude Sonnet 5.5 (the plan's default model) rejects non-default sampling and `thinking: disabled`; with adaptive thinking a 500-token cap could be spent on thinking. `between_tools` is sent only for the default model. See open-questions #1. · Alternative: follow the plan literally (would 400 on a real call).
28. **The validator compares canonical tokens:** sign + `$` + digits exactly as written + unit, where only spelling noise is normalised ("20.0 points" = "20.0 pts", "6.2 %" = "6.2%", Unicode minus = "-"). Digits, decimals and thousands separators must match exactly, and `k`/`m`/`bn` suffixes are kept, so "$12.5k" never matches "$12,480". Spelled-out numbers ("three jobs") aren't checked. · Catches invented and re-rounded figures without rejecting harmless wording. · Alternative: numeric tolerance (would accept re-rounding).
29. **The allow-list is every number in the run's facts** (overview plus every flagged job), not only the facts the model fetched. · Any number in the list was computed by Python, so it's true; this keeps the rule simple to explain. · Alternative: per-fetch allow-list.
30. **`demo-bad` invents `$13,750`** (the first of a few candidates that isn't a real figure that day), so it's rejected on both sample dates. · `$15,000` is a real figure on 3 Nov (job 1042's dollars at risk), so it can't be used.
31. **Fallback reasons:** `ai_off`, `rejected_numbers`, `no_api_key`, `unreachable`, `timeout`, `rate_limited`, `auth_error`, `api_error`, `refusal`, `truncated`, `too_many_rounds`, `empty_answer`, `bad_response`. On a fallback the summary still records the attempted provider and model.
32. **No server-side refusal fallback (`fallbacks` beta) on the Claude request.** · A refusal already falls back to the verified template, and the prototype never calls the API; keeping the request minimal keeps the shape test simple. Reconsider before a real deployment.
33. **"No key" means `ANTHROPIC_API_KEY` is empty** (the plan's rule); the SDK's other credential sources (CLI profiles) aren't consulted, so nothing is ever called by accident. The real client uses a 20 s timeout and 1 retry.
34. **`agent/.env` is loaded by the CLI only, never overriding real env vars**; `MARGIN_WATCH_ENV_FILE` points elsewhere and an empty value disables it (tests do this, so a developer's `.env` can't change test results).
35. **The demo's phrasing varies per job by SHA-256 of the job id** (Python's `hash()` is salted per process), and it caps individual job sentences at 3 so the summary stays within 3–6 sentences.

## Dashboard (Phase 6)

36. **Dashboard E2E tests intercept `runs/*.json` and serve the committed fixtures** (Playwright `page.route`) instead of copying them into `static/runs/`. · The build stays the real build; tests can't depend on whatever was last synced; empty and malformed states need no special build. · Alternative: a test-only static dir.
37. **The dashboard is a client-rendered single page (`ssr = false`, prerendered shell, adapter-static)** that fetches the run files in the browser. · New runs appear after `sync-runs` without rebuilding. · Alternative: prerender each run at build time.
38. **Risk order is recomputed in the browser with the agent's rule** (status, $ at risk desc, id) so "Status" sorting always restores it, whatever order the rows are in.
39. **Dashboard deltas (since last run) are computed in TypeScript from the run files' numbers** (counts, cents, points). This is display arithmetic in code, not AI maths; the model never sees or writes them.
40. **"Call today" list in the summary card** (added during the visual review): LOSS and AT_RISK jobs with PM and $ at risk. · Directly answers the brief's 5-second question; the summary prose stays for context.
41. **SvelteKit 3.1 / Svelte 5 / Vite 8 / Tailwind 4** from `npx sv create` + `sv add` (current stable on 3 Nov 2026). Components use scoped CSS on CSS-variable tokens; Tailwind supplies the reset and `sr-only`. The system font stack (Inter if installed) avoids a network font.
42. **Playwright runs on port 4174** so it never collides with `make demo` on 4173.

## CI, demo and hand-over (Phase 7 and Final)

43. **`make demo` simulates the two scheduled 6:30 AM runs** (`--generated-at <date>T06:30:00+11:00`) so the dashboard, QA checklist and Loom script show the same stamps every time.
44. **`scripts/check_frozen_tests.py`** (new, not a guardrail file) runs in `make test` and CI: no test file that existed at any `tests-approved-*` tag may differ from the tag.
45. **CI uses Node 24 LTS and Python 3.12 via uv**, `uv sync --frozen` and `npm ci`, fetches tags for the frozen-test check, and uploads the Playwright report on failure.

## After hand-over

46. **The summary renders as short toned rows (AC-91) instead of one paragraph.** · Zeddrix found the single-paragraph demo summary exhausting to read. Splitting is purely presentational, so the verified text and the email are untouched. · Alternative: change the demo model to write paragraphs (would make the committed fixtures stale).
47. **CI actions bumped to `actions/checkout@v7` and `astral-sh/setup-uv@v10`** (both Node 24), clearing GitHub's Node 20 deprecation warning. `setup-node@v4` and `upload-artifact@v4` weren't flagged and stay as they are.
48. **The GitHub repo is private** (`zeddrix/margin-watch`). · The Loom script and OVERVIEW name a real person and the interview context. CI runs on private repos too.
