# margin-watch: specification

A one-day prototype for a Melbourne commercial air-conditioning and mechanical services contractor. **All data is fictional.** Sources are shaped like Simpro and Microsoft Graph; nothing connects to a real system.

## Users

- **Ops manager.** Reads the morning email and the dashboard every morning, and needs to know within 5 seconds which jobs need a phone call today.
- **Managing director.** Wants the overview: how many jobs are slipping, dollars at risk, average forecast margin, and whether it's getting better or worse.

## Domain model (loosely shaped like Simpro)

A snapshot file holds `snapshot_date` (ISO date), a `source` note and a list of `jobs`.

**Job**

| Field | Type | Notes |
|---|---|---|
| `id` | string, required, unique in a file | Simpro-style job number, e.g. `"1042"` |
| `name`, `client`, `site`, `stage`, `project_manager` | string, required | |
| `quoted_sell_ex_gst` | Decimal or `null` | AUD, ex GST |
| `percent_complete` | Decimal or `null` | 0 to 100, one value for the whole job |
| `cost_centres` | list of CostCentre (may be empty) | |

**CostCentre**

| Field | Type | Notes |
|---|---|---|
| `name` | string, required | Labour, Materials, Subcontractors, Equipment hire |
| `estimated_cost` | Decimal or `null` | AUD |
| `actual_cost_to_date` | Decimal or `null` | AUD |
| `estimated_hours`, `actual_hours`, `hourly_rate` | Decimal, optional | Labour only; shown for context, never used in the maths |

Money in files is a string or number; it is always parsed to `Decimal` (never float). A structurally broken file (not JSON, missing a required string field, wrong type, duplicate job id) is an **invalid input file**: the loader raises `SourceError` with a message naming the job id and the field, and the CLI exits 2. A job whose *values* are missing or impossible is not an error: it becomes NEEDS_REVIEW.

## Formulas

All maths is Python `Decimal`. Percentages are stored in percent units (20 means 20%), so the formulas below include `× 100`. This is identical to the fraction form in the plan.

- `estimated_total = Σ estimated_cost`
- `quoted_margin_pct = (sell − estimated_total) / sell × 100`
- per cost centre, `forecast_at_completion`:
  - `0 < percent_complete < 100`: `max(estimated_cost, actual_to_date / percent_complete × 100)`, labelled **"projected at current burn rate"**. It is never below the estimate.
  - `percent_complete = 100`: `actual_to_date` (may be below the estimate).
  - `percent_complete = 0` (only reachable when no actual cost is above 0): `estimated_cost`.
- `forecast_total = Σ forecast_at_completion`
- `forecast_margin_pct = (sell − forecast_total) / sell × 100`
- `margin_erosion_pts = quoted_margin_pct − forecast_margin_pct`
- `dollars_at_risk = max(0, forecast_total − estimated_total)`
- per cost centre: `overrun_dollars = forecast − estimated`; `overrun_pct = (forecast / estimated − 1) × 100`, or `null` when the estimate is 0 (shown as "n/a").

Thresholds are compared against the **unrounded** values. Rounding happens only when formatting.

### Portfolio figures (per run)

- counts per status, `total_jobs`
- `jobs_needing_action` = LOSS + AT_RISK; `jobs_to_review` = NEEDS_REVIEW
- `total_dollars_at_risk` = Σ dollars_at_risk over every job that isn't NEEDS_REVIEW
- `average_forecast_margin_pct` = sell-weighted: `(Σ sell − Σ forecast_total) / Σ sell × 100` over every job that isn't NEEDS_REVIEW; `null` if there are none.

### Formatting (only for display)

- Money: AUD, rounded half-up to whole dollars, thousands separators: `$12,480`, `-$1,250`, `$0`. Files (run JSON, Excel cells) keep cents.
- Percent: one decimal, half-up (away from zero): `6.25 → "6.3%"`, `-1.25 → "-1.3%"`. A value that rounds to zero never shows a minus sign: `-0.04 → "0.0%"`.
- Points: one decimal plus ` pts`: `8.0 pts`.
- Dates: `Wed 4 Nov 2026`.

## Status rules

Thresholds live in `config/thresholds.toml`:

| Key | Default | Rule |
|---|---|---|
| `at_risk_margin_pct` | 10.0 | AT_RISK when forecast margin **<** this |
| `at_risk_erosion_pts` | 8.0 | AT_RISK when erosion **≥** this |
| `watch_erosion_pts` | 3.0 | WATCH when erosion **≥** this |
| `watch_overrun_pct` | 15.0 | WATCH when any cost centre's overrun_pct **≥** this |

Checked in this order; the first match wins.

1. **NEEDS_REVIEW** (checked first; the first problem found is the reason, and no metrics are calculated, so nothing is guessed):

   | Order | `review_code` | When | Reason text |
   |---|---|---|---|
   | 1 | `no_cost_centres` | the job has no cost centres | `Job has no cost centres.` |
   | 2 | `missing_sell` | sell is null | `Quoted sell price is missing.` |
   | 3 | `non_positive_sell` | sell ≤ 0 | `Quoted sell price is $0; it must be above $0.` (actual value) |
   | 4 | `missing_cost` | any estimated or actual cost is null | `Labour actual cost to date is missing.` / `Labour estimated cost is missing.` |
   | 5 | `negative_cost` | any estimated or actual cost < 0 | `Materials actual cost to date is negative (-$1,250).` |
   | 6 | `missing_percent_complete` | percent complete is null | `Percent complete is missing, so the forecast can't be worked out.` |
   | 7 | `percent_out_of_range` | percent complete < 0 or > 100 | `Percent complete is 112.0%, outside 0 to 100%.` |
   | 8 | `zero_percent_with_costs` | percent complete is 0 and any actual cost > 0 | `Percent complete is 0% but $1,500 has been spent.` (Σ actual) |

   Within a rule, cost centres are checked in file order, estimated cost before actual cost. The plan lists these problems in a different order; costs are checked before percent complete so the 0% rule only ever sums known, non-negative actuals (see decisions).
2. **LOSS:** forecast margin < 0.
3. **AT_RISK:** forecast margin < 10% (checked first for the reason), or erosion ≥ 8 pts.
4. **WATCH:** erosion ≥ 3 pts (checked first for the reason), or any cost centre overrun ≥ 15%.
5. **ON_TRACK:** otherwise.

**Main driver** (LOSS, AT_RISK and WATCH only): the cost centre with the largest `overrun_dollars`, ties broken alphabetically by name. If no cost centre has an overrun above $0, there is no main driver. ON_TRACK and NEEDS_REVIEW jobs have no main driver.

**Reason text** (numbers formatted as above):

| Trigger | Reason |
|---|---|
| LOSS | `Heading for a loss: forecast margin {f} against {q} quoted.` |
| AT_RISK, margin | `Forecast margin {f} is below the {10.0%} floor (quoted {q}).` |
| AT_RISK, erosion | `Margin has eroded {e} since quote, past the {8.0 pts} limit.` |
| WATCH, erosion | `Margin has eroded {e} since quote.` |
| WATCH, overrun | `{cost centre} is projected {$} ({pct}) over estimate.` (the cost centre with the largest overrun_pct at or over the limit; ties alphabetical) |
| ON_TRACK | `Forecast margin {f} against {q} quoted, within thresholds.` |

Flagged jobs with a main driver then get ` Main driver: {cost centre}, projected {$} ({pct}) over estimate.`, unless the WATCH-overrun sentence already names that cost centre. When overrun_pct is null the ` ({pct})` part is left out.

**Sort order:** LOSS, AT_RISK, WATCH, NEEDS_REVIEW, ON_TRACK; then dollars at risk descending (NEEDS_REVIEW counts as 0); then job id ascending.

## Sample data

`data/sample/jobs-2026-11-03.json` and `data/sample/jobs-2026-11-04.json`: the same 14 fictional jobs a day apart. Labour is costed at $100/h in the sample. Job 1038 gets worse (WATCH → AT_RISK); job 1036 gets better (WATCH → ON_TRACK: progress jumped from 40% to 55% after a milestone sign-off). Job 1040 sits **exactly on a threshold**: Equipment hire is forecast at $2,300 against a $2,000 estimate, an overrun of exactly 15.0%, so it is WATCH (≥).

Expected results, **calculated by hand** (sell, Σ estimate, Σ forecast in AUD; q = quoted margin, f = forecast margin, e = erosion):

### 4 Nov 2026 (7 ON_TRACK, 2 WATCH, 2 AT_RISK, 1 LOSS, 2 NEEDS_REVIEW)

| # | Job | PM | %  | Sell | Σ est | Σ forecast | q | f | e (pts) | $ at risk | Status | Main driver | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1042 Chiller replacement, cold-storage warehouse | Dave Kowalski | 60 | 80,000 | 66,000 | 82,000 | 17.5 | −2.5 | 20.0 | 16,000 | LOSS | Labour (36,000 vs 24,000) | Heading for a loss: forecast margin -2.5% against 17.5% quoted. Main driver: Labour, projected $12,000 (50.0%) over estimate. |
| 2 | 1038 Level 4 fit-out: VRF install | Priya Nair | 45 | 250,000 | 200,000 | 223,000 | 20.0 | 10.8 | 9.2 | 23,000 | AT_RISK | Labour (90,000 vs 72,000) | Margin has eroded 9.2 pts since quote, past the 8.0 pts limit. Main driver: Labour, projected $18,000 (25.0%) over estimate. |
| 3 | 1035 Ductwork upgrade, medical centre | Sam Okafor | 80 | 125,000 | 100,000 | 114,000 | 20.0 | 8.8 | 11.2 | 14,000 | AT_RISK | Labour (50,000 vs 40,000) | Forecast margin 8.8% is below the 10.0% floor (quoted 20.0%). Main driver: Labour, projected $10,000 (25.0%) over estimate. |
| 4 | 1033 Rooftop package unit replacement, school | Tom Reilly | 50 | 160,000 | 120,000 | 128,000 | 25.0 | 20.0 | 5.0 | 8,000 | WATCH | Labour (45,600 vs 40,000) | Margin has eroded 5.0 pts since quote. Main driver: Labour, projected $5,600 (14.0%) over estimate. |
| 5 | 1040 Car park exhaust fans | Mei Lin Tan | 50 | 60,000 | 45,000 | 45,300 | 25.0 | 24.5 | 0.5 | 300 | WATCH | Equipment hire (2,300 vs 2,000) | Equipment hire is projected $300 (15.0%) over estimate. |
| 6 | 1039 Q4 preventive maintenance contract | Sam Okafor | null | 48,000 | — | — | — | — | — | — | NEEDS_REVIEW | — | Percent complete is missing, so the forecast can't be worked out. |
| 7 | 1044 Cooling tower water treatment upgrade | Dave Kowalski | 30 | 35,000 | — | — | — | — | — | — | NEEDS_REVIEW | — | Materials actual cost to date is negative (-$1,250). |
| 8 | 1037 Office tower AHU refurbishment | Priya Nair | 60 | 200,000 | 160,000 | 165,000 | 20.0 | 17.5 | 2.5 | 5,000 | ON_TRACK | — | Forecast margin 17.5% against 20.0% quoted, within thresholds. |
| 9 | 1031 Boiler and hydronic heating upgrade, aged-care home | Tom Reilly | 100 | 110,000 | 88,000 | 85,800 | 20.0 | 22.0 | −2.0 | 0 | ON_TRACK | — | Forecast margin 22.0% against 20.0% quoted, within thresholds. |
| 10 | 1032 Split system installs, childcare centre | Mei Lin Tan | 0 | 25,000 | 20,000 | 20,000 | 20.0 | 20.0 | 0.0 | 0 | ON_TRACK | — | Forecast margin 20.0% against 20.0% quoted, within thresholds. |
| 11 | 1034 Kitchen exhaust and make-up air, restaurant | Sam Okafor | 70 | 40,000 | 32,000 | 32,000 | 20.0 | 20.0 | 0.0 | 0 | ON_TRACK | — | Forecast margin 20.0% against 20.0% quoted, within thresholds. |
| 12 | 1036 Server room precision cooling | Priya Nair | 55 | 90,000 | 72,000 | 72,000 | 20.0 | 20.0 | 0.0 | 0 | ON_TRACK | — | Forecast margin 20.0% against 20.0% quoted, within thresholds. |
| 13 | 1041 Cool room evaporator replacement, supermarket | Tom Reilly | 90 | 36,000 | 27,000 | 27,000 | 25.0 | 25.0 | 0.0 | 0 | ON_TRACK | — | Forecast margin 25.0% against 25.0% quoted, within thresholds. |
| 14 | 1043 BMS controls upgrade, university library | Mei Lin Tan | 25 | 75,000 | 60,000 | 60,000 | 20.0 | 20.0 | 0.0 | 0 | ON_TRACK | — | Forecast margin 20.0% against 20.0% quoted, within thresholds. |

Portfolio: jobs needing action 3, to review 2, total dollars at risk $66,300, average forecast margin (196,900 / 1,251,000) = 15.7394…% → `15.7%`.

Worked example, job 1042: Labour 21,600 / 60 × 100 = 36,000; Materials 19,800 / 60 × 100 = 33,000; Subcontractors 4,800 / 60 × 100 = 8,000 (= estimate); Equipment hire 3,000 / 60 × 100 = 5,000. Σ forecast 82,000. q = (80,000 − 66,000) / 80,000 = 17.5%; f = (80,000 − 82,000) / 80,000 = −2.5%; e = 20.0 pts; at risk = 82,000 − 66,000 = 16,000.

### 3 Nov 2026 (6 ON_TRACK, 4 WATCH, 1 AT_RISK, 1 LOSS, 2 NEEDS_REVIEW)

Rows that differ from 4 Nov (all others have the same status, figures and reason, only with smaller actuals and an earlier percent complete):

| # | Job | % | Σ forecast | q | f | e | $ at risk | Status | Reason |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1042 | 50 | 81,000 | 17.5 | −1.25 | 18.75 | 15,000 | LOSS | Heading for a loss: forecast margin -1.3% against 17.5% quoted. Main driver: Labour, projected $11,000 (45.8%) over estimate. |
| 2 | 1035 | 75 | 114,000 | 20.0 | 8.8 | 11.2 | 14,000 | AT_RISK | (same as 4 Nov) |
| 3 | 1038 | 40 | 212,000 | 20.0 | 15.2 | 4.8 | 12,000 | WATCH | Margin has eroded 4.8 pts since quote. Main driver: Labour, projected $12,000 (16.7%) over estimate. |
| 4 | 1033 | 45 | 128,000 | 25.0 | 20.0 | 5.0 | 8,000 | WATCH | (same as 4 Nov) |
| 5 | 1036 | 40 | 76,500 | 20.0 | 15.0 | 5.0 | 4,500 | WATCH | Margin has eroded 5.0 pts since quote. Main driver: Materials, projected $4,500 (10.0%) over estimate. |
| 6 | 1040 | 40 | 45,300 | 25.0 | 24.5 | 0.5 | 300 | WATCH | (same as 4 Nov) |
| 7–8 | 1039, 1044 | | | | | | | NEEDS_REVIEW | (same as 4 Nov) |
| 9–14 | 1037, 1031, 1032, 1034, 1041, 1043 | | | | | | | ON_TRACK | (same as 4 Nov) |

Portfolio: jobs needing action 2, to review 2, total dollars at risk $58,800, average forecast margin (204,400 / 1,251,000) = 16.3389…% → `16.3%`.

## Outputs per run

- `output/runs/<as_of>.json`: the run (schema below). `output/runs/index.json`: every run, newest first. These are the dashboard's only inputs.
- `output/margin-report-<as_of>.xlsx`
- `output/email/graph-sendmail-<as_of>.json` (Graph `sendMail` request body) and `output/email/preview-<as_of>.html`

The run JSON schema is pinned down in the Phase 4 acceptance criteria.

## Summary flow

1. Python builds a **facts object**: every number is a pre-formatted string (`"$12,000"`, `"-2.5%"`, `"20.0 pts"`).
2. The model is called through `ModelClient` with one tool, `get_job_facts(job_id)`, in a shared tool-use loop (at most 6 rounds).
3. The **validator** extracts every number in the model's text; each must exactly match a number in the facts.
4. On any failure (rejected number, no key, unreachable, timeout, error, too many rounds) the **template summary** is used and the reason is recorded.

Run JSON `summary` block: `text`, `source` (`ai_verified` | `template`), `provider` (`demo` | `demo-bad` | `local` | `claude` | `none`), `model`, `fallback_reason`, `rejected_tokens`.

## Interfaces

- `JobSource` (Protocol, `load() -> Snapshot`): `SampleFileSource(path)` now. `SimproSource` is documented only (Simpro REST API: jobs and cost centres, OAuth 2.0, webhooks to re-run on job changes).
- `Mailer`: `DryRunMailer` now (writes the payload and a preview, sends nothing). `GraphMailer` is documented only: an Entra ID app registration with OAuth 2.0 delegated `Mail.Send` calling `POST /me/sendMail`.
- `ModelClient`: `DemoModelClient` (`demo`, `demo-bad`), `OpenAICompatibleClient` (`local`), `AnthropicClient` (`claude`).

## CLI

`margin-watch run [--source PATH] [--as-of YYYY-MM-DD] [--ai demo|demo-bad|local|claude|off]`

- `--source` defaults to `sample_source` in `config/settings.toml`. `--as-of` defaults to the file's `snapshot_date`. `--ai` defaults to `MARGIN_WATCH_AI`, then `demo`.
- Exit codes: 0 ok, 2 invalid input file, 1 unexpected error. A NEEDS_REVIEW job isn't an error.

## Out of scope

Real Simpro, Graph or LLM calls; auth; quoting; invoicing; editing data; multi-user.
