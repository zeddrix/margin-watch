# Acceptance criteria

The contract. Each later phase turns its bullets into numbered criteria before writing its tests, so every ID here always has a test (`scripts/check_test_integrity.py` enforces it). Money is AUD. Unless a criterion says otherwise, default thresholds apply (AT_RISK below 10% forecast margin or at/above 8 pts erosion; WATCH at/above 3 pts erosion or at/above 15% cost centre overrun). "100% complete" makes forecast equal actual, which keeps boundary examples exact.

## Phase 2: calculations and status

### Forecasting and margins

**AC-01 Quoted margin.** Given a job with sell $100,000 and cost centres Labour (estimate $60,000) and Materials (estimate $20,000), when its metrics are calculated, then the estimated total is $80,000 and the quoted margin is exactly 20%.

**AC-02 Burn-rate forecast.** Given a job 40% complete with Labour estimate $10,000 and actual $5,000, when its metrics are calculated, then Labour's forecast at completion is $12,500 ("projected at current burn rate"), its overrun is $2,500 and its overrun is 25%.

**AC-03 Forecast never below estimate while in progress.** Given a job 50% complete with Labour estimate $10,000 and actual $2,000, when its metrics are calculated, then Labour's forecast is $10,000, overrun $0 and overrun 0%.

**AC-04 Complete jobs use actuals.** Given a job 100% complete with Labour estimate $10,000, when actual is $8,000 then the forecast is $8,000 with overrun −$2,000 (−20%); when actual is $12,000 then the forecast is $12,000 with overrun $2,000 (20%).

**AC-05 Not started.** Given a job 0% complete whose actual costs are all $0, with Labour estimate $10,000, when it is assessed, then Labour's forecast is $10,000 and the job is not NEEDS_REVIEW.

**AC-06 Job forecast margin, erosion and dollars at risk.** Given sell $100,000, 50% complete, Labour estimate $50,000 / actual $30,000 and Materials estimate $30,000 / actual $15,000, when its metrics are calculated, then the forecast total is $90,000, the forecast margin is 10%, the quoted margin 20%, erosion 10 pts and dollars at risk $10,000.

**AC-07 Dollars at risk is never negative.** Given sell $100,000, 100% complete, estimate $80,000 and actual $70,000 (one cost centre), when its metrics are calculated, then dollars at risk is $0, forecast margin 30% and erosion −10 pts.

**AC-08 Overrun % undefined for a zero estimate.** Given a job 100% complete whose Equipment hire has estimate $0 and actual $500, when its metrics are calculated, then Equipment hire's overrun is $500 and its overrun % is null (not a number, not an error).

### Status thresholds (below / at / above)

**AC-09 LOSS below 0%.** Given sell $100,000, 100% complete, one cost centre with estimate $90,000: when actual is $100,001 (forecast margin −0.001%) then the status is LOSS; when actual is $100,000 (forecast margin exactly 0%) the status is not LOSS (it is AT_RISK).

**AC-10 AT_RISK below a 10% forecast margin.** Given sell $100,000, 100% complete, one cost centre whose estimate equals its actual (so erosion is 0): at $90,010 (margin 9.99%) the status is AT_RISK; at $90,000 (exactly 10%) it is ON_TRACK; at $89,990 (10.01%) it is ON_TRACK.

**AC-11 AT_RISK at 8 pts of erosion.** Given sell $100,000, 100% complete, Labour estimate $70,000 (quoted 30%): actual $77,990 (erosion 7.99 pts) is WATCH; actual $78,000 (exactly 8 pts) is AT_RISK; actual $78,010 (8.01 pts) is AT_RISK. Forecast margins stay above 10% and overruns below 15%.

**AC-12 WATCH at 3 pts of erosion.** Same job: actual $72,990 (2.99 pts) is ON_TRACK; $73,000 (exactly 3 pts) is WATCH; $73,010 (3.01 pts) is WATCH.

**AC-13 WATCH at a 15% cost centre overrun.** Given sell $100,000, 100% complete, Labour estimate = actual $50,000, Equipment hire estimate $2,000: actual $2,299.80 (14.99%) is ON_TRACK; $2,300 (exactly 15%) is WATCH; $2,300.20 (15.01%) is WATCH. Erosion stays below 3 pts.

**AC-14 Precedence.** Given a job that is heading for a loss and also has erosion ≥ 8 pts and an overrun ≥ 15%, its status is LOSS. Given the same job with one negative actual cost, its status is NEEDS_REVIEW.

### NEEDS_REVIEW (never guess)

**AC-15 Missing percent complete.** Given a job whose percent complete is null, then the status is NEEDS_REVIEW, `review_code` is `missing_percent_complete` and the reason is `Percent complete is missing, so the forecast can't be worked out.`

**AC-16 Percent complete out of range.** Given percent complete 112, the status is NEEDS_REVIEW, code `percent_out_of_range`, reason `Percent complete is 112.0%, outside 0 to 100%.`; 100.01 and −5 are also NEEDS_REVIEW (reason for −5: `Percent complete is -5.0%, outside 0 to 100%.`); exactly 100 is not.

**AC-17 0% complete but money spent.** Given percent complete 0 and Labour actual $1,500, the status is NEEDS_REVIEW, code `zero_percent_with_costs`, reason `Percent complete is 0% but $1,500 has been spent.`

**AC-18 Negative cost.** Given Materials actual −$1,250, the status is NEEDS_REVIEW, code `negative_cost`, reason `Materials actual cost to date is negative (-$1,250).`; given Labour estimate −$100, reason `Labour estimated cost is negative (-$100).`

**AC-19 Missing cost.** Given Labour actual null, the status is NEEDS_REVIEW, code `missing_cost`, reason `Labour actual cost to date is missing.`; given Labour estimate null, reason `Labour estimated cost is missing.`

**AC-20 Sell price missing or not above zero.** Sell null gives code `missing_sell`, reason `Quoted sell price is missing.`; sell $0 gives code `non_positive_sell`, reason `Quoted sell price is $0; it must be above $0.`; sell −$500 gives reason `Quoted sell price is -$500; it must be above $0.`

**AC-21 No cost centres.** Given a job with no cost centres, the status is NEEDS_REVIEW, code `no_cost_centres`, reason `Job has no cost centres.`

**AC-22 First problem wins, nothing is guessed.** Given a job with a negative actual cost **and** a missing percent complete, the reason is the negative cost. Given sell $0 and no cost centres, the code is `no_cost_centres`. Every NEEDS_REVIEW job has no metrics and no main driver.

### Main driver, reasons, order

**AC-23 Main driver.** For a flagged job: Materials over by $3,000 (10%) beats Equipment hire over by $1,000 (50%), because dollars count, not percent. Labour and Materials both over by $2,000: Labour (alphabetical). An AT_RISK job with no cost centre over its estimate (sell $100,000, estimate = actual $95,000, 100% complete) has no main driver. An ON_TRACK job with an overrun has no main driver.

**AC-24 Reason text.** Given sell $100,000, 100% complete, the reasons are exactly:
- LOSS (Labour est $70,000 actual $90,000, Materials est = actual $12,000): `Heading for a loss: forecast margin -2.0% against 18.0% quoted. Main driver: Labour, projected $20,000 (28.6%) over estimate.`
- AT_RISK on margin (estimate = actual $95,000, Labour): `Forecast margin 5.0% is below the 10.0% floor (quoted 5.0%).`
- AT_RISK on erosion (Labour est $70,000 actual $79,000): `Margin has eroded 9.0 pts since quote, past the 8.0 pts limit. Main driver: Labour, projected $9,000 (12.9%) over estimate.`
- WATCH on erosion (Labour est $70,000 actual $74,000): `Margin has eroded 4.0 pts since quote. Main driver: Labour, projected $4,000 (5.7%) over estimate.`
- WATCH on overrun, same cost centre (Labour est = actual $50,000, Equipment hire est $2,000 actual $2,400): `Equipment hire is projected $400 (20.0%) over estimate.`
- WATCH on overrun, different driver (Labour est $50,000 actual $52,000, Equipment hire est $1,000 actual $1,200): `Equipment hire is projected $200 (20.0%) over estimate. Main driver: Labour, projected $2,000 (4.0%) over estimate.`
- ON_TRACK (Labour est = actual $80,000): `Forecast margin 20.0% against 20.0% quoted, within thresholds.`

**AC-25 Sort order.** Given jobs in mixed order, sorting gives LOSS, AT_RISK, WATCH, NEEDS_REVIEW, ON_TRACK; within a status, dollars at risk descending; then job id ascending.

### Config, loading and sample data

**AC-26 Thresholds come from config.** `config/thresholds.toml` loads as 10 / 8 / 3 / 15. Given a custom file with `at_risk_margin_pct = 12`, a job with an 11% forecast margin and no erosion is AT_RISK. A file missing a key raises a config error that names the key.

**AC-27 Sample loader.** Loading `data/sample/jobs-2026-11-04.json` gives snapshot date 2026-11-04 and 14 jobs; job 1042 has sell `Decimal("80000.00")`, 4 cost centres, and Labour actual `Decimal("21600.00")`. Money given as a JSON number such as `0.1` loads as exactly `Decimal("0.1")`.

**AC-28 Invalid files fail loudly and clearly.** A missing file, a file that isn't JSON, a job missing `client`, a non-numeric `estimated_cost` and a duplicate job id each raise `SourceError`; the message names the job id and the field (or the file, for file-level problems).

**AC-29 Sample, 4 Nov.** Assessing `jobs-2026-11-04.json` gives exactly the order, statuses, main drivers, reasons and figures in the 4 Nov table in `docs/spec.md` (1042 LOSS; 1038, 1035 AT_RISK; 1033, 1040 WATCH; 1039, 1044 NEEDS_REVIEW; 1037, 1031, 1032, 1034, 1036, 1041, 1043 ON_TRACK).

**AC-30 Sample, 3 Nov.** Assessing `jobs-2026-11-03.json` gives 1042 LOSS; 1035 AT_RISK; 1038, 1033, 1036, 1040 WATCH; 1039, 1044 NEEDS_REVIEW; then the 6 ON_TRACK jobs, with the figures in the 3 Nov table.

**AC-31 Portfolio figures.** 4 Nov: counts 1 / 2 / 2 / 2 / 7, jobs needing action 3, to review 2, total dollars at risk $66,300, average forecast margin 15.7394% (to 4 dp). 3 Nov: 1 / 1 / 4 / 2 / 6, needing action 2, total at risk $58,800, average 16.3389%. A run where every job is NEEDS_REVIEW has total at risk $0 and no average.

**AC-32 Property: overruns never improve margin.** For any job (hypothesis-generated) in which every cost centre's forecast is at or above its estimate, the forecast margin is at or below the quoted margin and dollars at risk equals the sum of overrun dollars.

**AC-33 Display formatting.** Money: 12,480.50 → `$12,481`; 12,480.49 → `$12,480`; −1,250 → `-$1,250`; 0 → `$0`. Percent: 6.25 → `6.3%`; −1.25 → `-1.3%`; −0.04 → `0.0%`; 15 → `15.0%`. Points: 8 → `8.0 pts`; 18.75 → `18.8 pts`. Date: 2026-11-04 → `Wed 4 Nov 2026`.

## Phase 4: outputs and CLI (to be numbered in Phase 4)

- Run JSON schema: schema version, as_of, generated_at, source, thresholds used, counts per status, portfolio figures, every job with all fields, cost centres, status, reason, review code and main driver, and the summary block.
- `runs/index.json` lists runs newest first, with counts and dollars at risk; re-running a date replaces its entry.
- Excel "Summary", "Jobs" and "Cost centres" sheets: values, AUD and % number formats, frozen header, autofilter, column widths, status fill colour plus the status word, sort order.
- The exact Graph `POST /me/sendMail` payload shape, recipient from `config/settings.toml`, the subject line format.
- The email lists only non-ON_TRACK jobs, carries the summary with its provider label, and a footer; its HTML is a snapshot.
- `DryRunMailer` writes the JSON and HTML preview and opens no socket.
- Template summary wording (snapshot).
- CLI: `--as-of` determinism, exit codes 0 / 2 / 1, readable error for a malformed file, `--ai off` uses the template.

## Phase 5: summary, providers and number verification (to be numbered in Phase 5)

- Facts object with every number as a pre-formatted string.
- Demo model: tool calls first, then text built only from tool results; deterministic; verified.
- `demo-bad`: one invented number is rejected, template used, rejected tokens and fallback reason recorded.
- The validator rejects an invented number and a re-rounded number; identifiers and dates don't trip it.
- Tool-use loop: unknown job id returns a tool error; at most 6 rounds.
- Every fallback path: no API key, unreachable server, timeout, API error, too many rounds, empty answer.
- Anthropic and OpenAI-compatible request shapes and response parsing, with fakes.

## Phase 6: dashboard (to be numbered in Phase 6)

- Top bar with wordmark, run date and time, "Sample data" pill and run picker.
- KPI tiles matching the run, with "since last run" context.
- Summary card with provider badge, "Why?" for rejected answers, job links that open the drawer.
- Jobs table: risk order, sortable columns with aria-sort, filter chips with counts, search, "x of 14 jobs", worse-since-last-run marker, keyboard access.
- Job drawer: dialog semantics, focus trap, Esc/backdrop close, focus return, bullet charts, NEEDS_REVIEW guidance.
- Empty, loading and error states; responsive cards at 390px; dark theme; accessibility (axe).
