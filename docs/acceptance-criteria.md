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

## Phase 4: outputs and CLI

Unless stated, "the 4 Nov run" means `margin-watch run --source data/sample/jobs-2026-11-04.json --ai off --generated-at 2026-11-04T06:30:00+11:00 --output-dir <tmp>`. JSON money is a number rounded to cents; JSON percentages and points are numbers rounded to 4 decimals.

### Run JSON

**AC-34 Run JSON top level.** The 4 Nov run writes `runs/2026-11-04.json` with exactly the keys `schema_version` (1), `as_of` ("2026-11-04"), `generated_at` ("2026-11-04T06:30:00+11:00"), `source` (`{"kind": "sample_file", "name": "jobs-2026-11-04.json", "sample_data": true}`), `thresholds` (`{"at_risk_margin_pct": 10.0, "at_risk_erosion_pts": 8.0, "watch_erosion_pts": 3.0, "watch_overrun_pct": 15.0}`), `counts` (`{"LOSS": 1, "AT_RISK": 2, "WATCH": 2, "NEEDS_REVIEW": 2, "ON_TRACK": 7}`), `portfolio` (`{"total_jobs": 14, "jobs_needing_action": 3, "jobs_to_review": 2, "total_dollars_at_risk": 66300.0, "average_forecast_margin_pct": 15.7394}`), `jobs` and `summary`.

**AC-35 Run JSON jobs.** `jobs` is in risk order (1042, 1038, 1035, 1033, 1040, 1039, 1044, 1037, 1031, 1032, 1034, 1036, 1041, 1043). Each job has `id`, `name`, `client`, `site`, `stage`, `project_manager`, `quoted_sell_ex_gst`, `percent_complete`, `status`, `reason`, `review_code`, `main_driver`, `estimated_total`, `forecast_total`, `quoted_margin_pct`, `forecast_margin_pct`, `margin_erosion_pts`, `dollars_at_risk` and `cost_centres` (each: `name`, `estimated_cost`, `actual_cost_to_date`, `forecast_at_completion`, `overrun_dollars`, `overrun_pct`, `estimated_hours`, `actual_hours`, `hourly_rate`). Job 1042 has sell 80000.0, percent 60.0, estimated 66000.0, forecast 82000.0, quoted 17.5, forecast margin −2.5, erosion 20.0, at risk 16000.0, and Labour 24000.0 / 21600.0 / 36000.0 / 12000.0 / 50.0 with hours 240.0 / 216.0 at 100.0. NEEDS_REVIEW job 1039 has `percent_complete` null, `review_code` "missing_percent_complete", every computed field null (including each cost centre's forecast and overruns), and its raw costs (Labour 30000.0 / 12000.0).

**AC-36 Run index.** After running 3 Nov and then 4 Nov into the same output dir, `runs/index.json` is `{"schema_version": 1, "runs": [...]}` with 4 Nov first; each entry has `as_of`, `file` ("2026-11-04.json"), `generated_at`, `counts`, `jobs_needing_action`, `total_dollars_at_risk` and `summary_source`. Re-running 3 Nov leaves exactly 2 entries, still 4 Nov first.

### Excel report (`margin-report-<as_of>.xlsx`)

**AC-37 Summary sheet.** Sheets are exactly "Summary", "Jobs", "Cost centres". On "Summary", column A labels map to column B values: "Run date" → the date 2026-11-04 (format `ddd d mmm yyyy`), "Source" → "jobs-2026-11-04.json", "Loss" 1, "At risk" 2, "Watch" 2, "Needs review" 2, "On track" 7, "Total jobs" 14, "Jobs needing action" 3, "Total dollars at risk" 66300 (AUD format), "Average forecast margin" 0.157394 (format `0.0%`), "Summary" → the summary text, "Written by" → "Template summary". A1 is "Margin Watch report" and the sheet says "Sample data".

**AC-38 Jobs sheet values.** Row 1 headers are exactly Job, Client, Site, PM, Sell, Quoted margin %, Forecast margin %, Erosion (pts), Dollars at risk, Status, Main driver, Reason. Rows 2–15 are in risk order. Row 2 is "1042 Chiller replacement, cold-storage warehouse", "Frostline Logistics", "Frostline cold store, Dandenong South", "Dave Kowalski", 80000, 0.175, −0.025, 20, 16000, "LOSS", "Labour", and the 1042 reason. The 1039 row has Sell 48000, empty quoted margin, forecast margin, erosion, dollars at risk and main driver cells, status "NEEDS REVIEW" and its reason. Status words: LOSS, AT RISK, WATCH, NEEDS REVIEW, ON TRACK.

**AC-39 Jobs sheet formatting.** Sell and Dollars at risk use `"$"#,##0.00`; the margin columns use `0.0%`; erosion uses `0.0`. Freeze panes at A2, autofilter `A1:L15`, bold header, column widths A 46, B 28, C 36, D 16, E 14, F 12, G 12, H 11, I 14, J 15, K 16, L 90, and Reason wraps. The status cell has a solid fill: LOSS `FCA5A5` (red), AT RISK `FDBA74` (amber), WATCH `FEF08A` (yellow), NEEDS REVIEW `CBD5E1` (slate), ON TRACK `86EFAC` (green), and shows the status word.

**AC-40 Cost centres sheet.** Headers exactly Job, Cost centre, Estimated, Actual to date, Forecast at completion, Overrun ($), Overrun %. One row per cost centre, jobs in risk order and cost centres in file order: 49 rows (2–50); row 2 is "1042 Chiller replacement, cold-storage warehouse", "Labour", 24000, 21600, 36000, 12000, 0.5. NEEDS_REVIEW rows have empty forecast and overrun cells. Money cells use `"$"#,##0.00`, Overrun % uses `0.0%`, freeze panes A2, autofilter `A1:G50`.

### Email (Microsoft Graph `sendMail`, dry run)

**AC-41 Graph payload shape.** `email/graph-sendmail-2026-11-04.json` is exactly `{"message": {"subject": ..., "body": {"contentType": "HTML", "content": ...}, "toRecipients": [{"emailAddress": {"address": "ops@example.com"}}]}, "saveToSentItems": true}`, with no other keys, and the recipient comes from `config/settings.toml` (`[email] to`).

**AC-42 Subject line.** 4 Nov: `Margin watch, Wed 4 Nov: 1 loss, 2 at risk, 2 to review`. 3 Nov: `Margin watch, Tue 3 Nov: 1 loss, 1 at risk, 2 to review`. Two losses read `2 losses`. A run with only WATCH and ON_TRACK jobs: `Margin watch, Wed 4 Nov: 1 on watch`. A run where every job is ON_TRACK (2 jobs): `Margin watch, Wed 4 Nov: all 2 jobs on track`.

**AC-43 Email body.** The 4 Nov email HTML (payload `content`) equals `agent/tests/snapshots/email-2026-11-04.html`: the summary paragraphs, the label line "Template summary", a table listing only the 7 non-ON_TRACK jobs in risk order (status word, job and client, PM, forecast margin, dollars at risk, reason; "—" for NEEDS_REVIEW figures), and a footer naming the run time (6:30 AM Melbourne), the source file, the Excel file, "Sample data only" and "Dry run". No ON_TRACK job id appears. `email/preview-2026-11-04.html` has the same HTML.

**AC-44 DryRunMailer sends nothing.** `DryRunMailer(dir).send(draft)` writes `graph-sendmail-<as_of>.json` (the payload, pretty-printed) and `preview-<as_of>.html`, returns both paths with `sent` false, and works while creating any socket raises an error.

### Template summary

**AC-45 Template summary wording.** For 4 Nov the template text equals `agent/tests/snapshots/template-summary-2026-11-04.txt`: an overview paragraph (counts and total overruns), one "Call {PM} about {id} {name}." paragraph per LOSS and AT_RISK job followed by its reason, and a final paragraph naming WATCH jobs and NEEDS_REVIEW jobs with their PMs. Paragraphs are separated by a blank line. For 2 ON_TRACK jobs with no overrun it is exactly `Of 2 jobs, 2 are on track.`; for one NEEDS_REVIEW job (PM "Ann Lee", id "X1", name "Pump swap") it is `Of 1 job, 1 needs a data check.` + blank line + `Data to check in Simpro: X1 Pump swap (Ann Lee).`

### CLI

**AC-46 Successful run.** The 4 Nov run exits 0, writes `runs/2026-11-04.json`, `runs/index.json`, `margin-report-2026-11-04.xlsx`, `email/graph-sendmail-2026-11-04.json` and `email/preview-2026-11-04.html`, and prints each path. Without `--as-of` the as-of date is the file's `snapshot_date`; with `--as-of 2026-11-05` the files are named for 2026-11-05 and `as_of` is "2026-11-05".

**AC-47 Deterministic.** Two runs of the same file with the same `--generated-at` into different dirs produce byte-identical run JSON, Graph JSON and preview HTML, and identical Excel cell values. With a different `--generated-at`, the run JSON differs only in `generated_at`.

**AC-48 Invalid input exits 2.** A missing file, a file that isn't JSON, and a job missing `client` each exit 2 with a readable message starting `Invalid input file:` that names the problem (the file, or the job id and field), print no traceback, and write no output files.

**AC-49 Unexpected errors exit 1.** When the output dir can't be created (it is an existing file), the run exits 1 with a message starting `Unexpected error:` and no traceback. A malformed `--as-of` such as `4/11/2026` is a usage error: exit 2 with a message naming the `YYYY-MM-DD` format and no traceback.

**AC-50 `--ai off` uses the template.** The 4 Nov run's `summary` is `{"text": <template text>, "source": "template", "provider": "none", "model": null, "fallback_reason": "ai_off", "rejected_tokens": []}`.

**AC-51 NEEDS_REVIEW isn't an error.** A file whose only two jobs are both NEEDS_REVIEW exits 0, with counts NEEDS_REVIEW 2, `average_forecast_margin_pct` null and total dollars at risk 0.0.

## Phase 5: summary, providers and number verification

"The 4 Nov report" is `build_report` on `jobs-2026-11-04.json` (as of 2026-11-04). Fakes stand in for every model; no test opens a network connection. The invented figure used by `demo-bad` is `$13,750`, which appears in neither sample run.

### Facts and the validator

**AC-52 Facts are pre-formatted strings.** `build_facts(report)` returns an `overview` and a `jobs` map in which every leaf value is a string. For 4 Nov: `run_date` "Wed 4 Nov 2026", `total_jobs` "14", `jobs_needing_action` "3", `jobs_to_review` "2", `total_dollars_at_risk` "$66,300", `average_forecast_margin` "15.7%", counts `{"loss": "1", "at_risk": "2", "watch": "2", "needs_review": "2", "on_track": "7"}`, and `flagged_jobs` listing the 7 jobs that aren't ON_TRACK in risk order. Job 1042's facts are exactly: job_id "1042", name, client, site, project_manager "Dave Kowalski", status "LOSS", percent_complete "60.0%", quoted_margin "17.5%", forecast_margin "-2.5%", margin_erosion "20.0 pts", dollars_at_risk "$16,000", main_driver "Labour", main_driver_overrun "$12,000", main_driver_overrun_pct "50.0%", reason (the spec text). NEEDS_REVIEW job 1039 has status "NEEDS_REVIEW", its review problem and a "what_to_check" hint, and no margin figures.

**AC-53 The validator accepts exact numbers.** With the 4 Nov facts, `Labour is $12,000 (50.0%) over and erosion is 20.0 pts, so 3 jobs need a call.` passes with no rejected tokens. Money, percentages, points, decimals and integers are all extracted.

**AC-54 The validator rejects invented numbers.** With the 4 Nov facts, `It is about $15,000 over.` is rejected with rejected tokens `["$15,000"]`; `Send 12 crews.` is rejected with `["12"]`; each rejected token is listed once, in order of appearance.

**AC-55 The validator rejects re-rounded numbers.** Given facts containing "6.2%", "$12,480", "8.1 pts" and "-2.5%": `6%`, `$12,500`, `8 pts`, `2.5%` and `$12.5k` are each rejected; the exact forms pass.

**AC-56 Identifiers and dates don't trip it.** Given facts with job_id "1042", name "Level 4 fit-out: VRF install" and run_date "Wed 4 Nov 2026", the text `Job 1042 (Level 4 fit-out, Q4 programme) on 4 Nov 2026.` passes. "Q4" isn't a number token.

**AC-57 Harmless spelling variants.** "20.0 points" matches the fact "20.0 pts", and a Unicode minus "−2.5%" matches "-2.5%". Nothing else is normalised.

### Demo model and the tool-use loop

**AC-58 Demo asks for facts first.** Given the 4 Nov facts message, `DemoModelClient().complete(...)` first returns no text and one `get_job_facts` call per flagged job, in risk order (1042, 1038, 1035, 1033, 1040, 1039, 1044).

**AC-59 Demo writes a verified summary.** `summarise(report, DemoModelClient(), provider="demo", model="demo-scripted-1")` for 4 Nov gives source `ai_verified`, provider `demo`, model `demo-scripted-1`, no fallback reason and no rejected tokens. The text has 3 to 6 sentences, its first sentence names "Dave Kowalski" and "1042", every number in it appears in the facts, and two runs produce identical text. The 3 Nov run is verified too.

**AC-60 demo-bad is caught.** `summarise(..., DemoModelClient(bad=True), provider="demo-bad", ...)` for 4 Nov and for 3 Nov gives source `template`, the template text, `rejected_tokens == ["$13,750"]` and `fallback_reason == "rejected_numbers"`.

**AC-61 Unknown job id is a tool error, not a crash.** A model that asks for `get_job_facts("9999")` gets a tool result with `is_error` true whose content names "9999"; the loop goes on, and when the model then writes a valid answer the summary is `ai_verified`. An unknown tool name gets an error result too.

**AC-62 At most 6 rounds.** A model that asks for a tool on every turn is called exactly 6 times, then the template is used with `fallback_reason "too_many_rounds"`.

**AC-63 Empty answers fall back.** A model whose final turn is empty or whitespace gives the template with `fallback_reason "empty_answer"`.

### Claude (Anthropic SDK), with a fake SDK client

**AC-64 Anthropic request shape and parsing.** `AnthropicClient` sends `messages.create` with `model` (default `claude-sonnet-5-5`, or `MARGIN_WATCH_MODEL`), `system` equal to `prompts/summary_system.md`, `tools` equal to the single `get_job_facts` tool (`name`, `description`, `input_schema` with a required string `job_id`), `max_tokens` 500, `thinking {"type": "between_tools"}` and **no** `temperature` (Claude Sonnet 5.5 rejects non-default sampling; see decisions). The follow-up request echoes the assistant `content` unchanged and sends one user message of `tool_result` blocks whose `tool_use_id` matches each `tool_use` id. `text` blocks become the answer; `tool_use` blocks become tool calls. A run with this fake is `ai_verified` with provider `claude`.

**AC-65 Anthropic failures fall back quietly.** No `ANTHROPIC_API_KEY` gives the template with `fallback_reason "no_api_key"` and no exception, and `margin-watch run --ai claude` without a key exits 0. The SDK's `APITimeoutError` gives `timeout`; `APIConnectionError` gives `unreachable`; `RateLimitError` gives `rate_limited`; any other `APIStatusError` (500) gives `api_error`; `stop_reason "refusal"` gives `refusal`; `stop_reason "max_tokens"` gives `truncated`. A real client built from a key uses a 20 s timeout.

### Local model (OpenAI-compatible), with `httpx.MockTransport`

**AC-66 Local request shape and parsing.** `OpenAICompatibleClient` POSTs to `{LOCAL_LLM_URL}/v1/chat/completions` with `model` = `LOCAL_LLM_MODEL`, `messages` starting with the system prompt then the facts message, `tools` `[{"type": "function", "function": {"name": "get_job_facts", ...}}]`, `max_tokens` 500 and `temperature` 0. `tool_calls` with JSON-string `arguments` become tool calls; the follow-up sends the assistant `tool_calls` and one `role: "tool"` message per result. A run with this transport is `ai_verified` with provider `local`.

**AC-67 Local failures fall back quietly.** A connection error gives `unreachable`, a timeout `timeout`, an HTTP 500 `api_error`, and a reply that isn't the expected JSON `bad_response`. `margin-watch run --ai local` against an unreachable server exits 0 with the template. The client uses a 30 s timeout.

### Wiring and labels

**AC-68 Provider selection.** `--ai` beats `MARGIN_WATCH_AI`, which beats the default `demo`. With no `--ai` and no env var, the 4 Nov run's summary is `ai_verified` by `demo`; with `MARGIN_WATCH_AI=off` it is the template; `--ai off` beats `MARGIN_WATCH_AI=demo`.

**AC-69 Labels say who wrote it.** Email and Excel show `Written by Demo AI · numbers verified` for a verified demo run and `Template summary · AI answer rejected` for a demo-bad run. The labels for verified local and Claude runs are `Written by Local model · numbers verified` and `Written by Claude · numbers verified`. A demo label never contains "Claude".

**AC-70 One reviewable system prompt.** `prompts/summary_system.md` exists and says: busy ops manager at an HVAC contractor, plain Australian English, 3 to 6 sentences, lead with what needs action today and who the PM is, use numbers exactly as given, never calculate, round, add, compare or estimate, leave out any number not in the facts, no greeting or sign-off. The demo, Anthropic and local clients all receive exactly this text as the system prompt.

## Phase 6: dashboard (to be numbered in Phase 6)

- Top bar with wordmark, run date and time, "Sample data" pill and run picker.
- KPI tiles matching the run, with "since last run" context.
- Summary card with provider badge, "Why?" for rejected answers, job links that open the drawer.
- Jobs table: risk order, sortable columns with aria-sort, filter chips with counts, search, "x of 14 jobs", worse-since-last-run marker, keyboard access.
- Job drawer: dialog semantics, focus trap, Esc/backdrop close, focus return, bullet charts, NEEDS_REVIEW guidance.
- Empty, loading and error states; responsive cards at 390px; dark theme; accessibility (axe).
