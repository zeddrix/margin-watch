# margin-watch: BUILD-PLAN.md

## How to start (Zeddrix)

Open a terminal in `~/Documents/margin-watch`, run `claude`, and paste this one prompt:

```text
Read CLAUDE.md, docs/testing-rules.md and BUILD-PLAN.md fully. Then build margin-watch by executing BUILD-PLAN.md phase by phase, autonomously, until the Final phase is complete. Don't stop to ask me anything: decide, log decisions in docs/decisions.md, log blockers in docs/open-questions.md, and keep going. Keep docs/progress.md updated after every phase. If you were interrupted earlier, resume from docs/progress.md and git log.
```

If the session ever stops part-way (context, crash, or you closed it), open `claude` again and paste the same prompt. It picks up from `docs/progress.md`.

When it's done, follow `docs/manual-qa-checklist.md`, then record the Loom with `docs/loom-script.md`.

---

## What we're building

`margin-watch` is a one-day prototype for a Melbourne commercial air-conditioning and mechanical services contractor. Every morning it:

1. reads job costing data (sample data **shaped like Simpro** jobs and cost centres),
2. calculates quoted margin, forecast margin and margin erosion for each job, **in code**,
3. flags jobs losing margin, and flags bad data for review instead of guessing,
4. writes an Excel report,
5. drafts the ops manager's morning email as a real **Microsoft Graph `sendMail` request body** (dry run, never sent),
6. has a model write a short plain-English summary through a real tool-use loop, then **checks every number against the computed facts**,
7. shows everything on a calm, clear internal dashboard.

**All data is fictional.** Nothing connects to Simpro, Outlook, Anthropic or any other external service while running the demo.

**Stack:** Python 3.12 (uv, pandas, openpyxl, pydantic, typer, httpx, anthropic SDK) for the agent. SvelteKit + TypeScript (strict) + Tailwind, static adapter, for the dashboard. GitHub Actions CI config (it runs once the repo is pushed; there's no remote yet).

### AI providers (no paid API)

`MARGIN_WATCH_AI` picks the model behind the summary:

| Value | What it does | Needs |
|---|---|---|
| `demo` (default) | **Built-in scripted demo model.** It goes through the real tool-use loop (asks `get_job_facts` for each flagged job, then writes sentences using the returned strings), so the validator and fallback paths run for real. Deterministic. | nothing |
| `demo-bad` | Same, but deliberately slips one invented number into its answer, to show the validator rejecting it. | nothing |
| `local` | OpenAI-compatible local server (e.g. LM Studio) at `LOCAL_LLM_URL`, model `LOCAL_LLM_MODEL`. | a running local server |
| `claude` | Anthropic Messages API with tool use, model `MARGIN_WATCH_MODEL` (default `claude-sonnet-5-5`). | `ANTHROPIC_API_KEY` |
| `off` | Template summary only. | nothing |

`local` and `claude` are implemented and unit-tested with fakes, but **never called for real** in this build. If one is selected and unavailable (no key, unreachable, timeout, error), the run falls back to the template and records why. The dashboard and email always say which provider wrote the summary ("Demo AI", "Local model", "Claude") and whether the numbers were verified. Never present the demo model as Claude.

---

## Phase 0: check the setup

The guardrails are already committed: `CLAUDE.md`, `docs/testing-rules.md`, `.claude/settings.json` (permissions allowlist + hook), `.claude/hooks/protect_tests.py`, `scripts/check_test_integrity.py`, `.gitignore`. Don't modify them.

1. Report versions: `git --version`, `uv --version`, `node --version`, `npm --version`. Python 3.12 comes from uv (`uv python install 3.12` if needed). The system `python3` (3.9+) runs the hook and the integrity script.
2. Confirm the hook is active: try to `Write` a file at `.claude/allow-test-edits`. It must be blocked. Record the result in `docs/progress.md`.
3. Create `docs/progress.md` (a table: phase, status, tests, commit, notes), `docs/decisions.md` and `docs/open-questions.md` (both with a one-line header).
4. Commit `chore: progress, decisions and open-questions logs`.

## Phase 1: plan (docs only)

**1. `docs/spec.md`**
- Users: ops manager (reads the email and dashboard every morning) and managing director (wants the overview).
- Domain model, loosely shaped like Simpro: `Job` (id, name, client, site, stage, project_manager, quoted_sell_ex_gst, percent_complete, cost_centres[]). `CostCentre` (name: Labour, Materials, Subcontractors, Equipment hire; estimated_cost; actual_cost_to_date; Labour also has estimated_hours, actual_hours, hourly_rate).
- Formulas, written out:
  - `quoted_margin_pct = (sell − Σ estimated_cost) / sell`
  - per cost centre: `forecast_at_completion = actual_to_date / percent_complete` when 0 < percent_complete < 100, labelled "projected at current burn rate". It's never below the estimate unless the job is 100% complete. At 100%, forecast = actual.
  - `forecast_margin_pct = (sell − Σ forecast) / sell`
  - `margin_erosion_pts = (quoted_margin_pct − forecast_margin_pct) × 100`
  - `dollars_at_risk = max(0, Σ forecast − Σ estimated)`
  - per cost centre: `overrun_pct = forecast / estimated − 1`, and `overrun_dollars = forecast − estimated`
- Status rules, thresholds in `config/thresholds.toml`, with `<` and `≥` stated exactly:
  - NEEDS_REVIEW (checked first): percent_complete missing; or 0 with actual costs > 0; or > 100; any negative cost; sell ≤ 0; no cost centres. Each has its own reason text.
  - LOSS: forecast margin < 0
  - AT_RISK: forecast margin < 10% OR erosion ≥ 8 pts
  - WATCH: erosion ≥ 3 pts OR any cost centre overrun ≥ 15%
  - ON_TRACK: otherwise
- Main driver of a flagged job: the cost centre with the largest overrun in dollars (ties: alphabetical).
- Sort order: LOSS, AT_RISK, WATCH, NEEDS_REVIEW, ON_TRACK, then dollars at risk descending, then job id.
- Two sample snapshots so the dashboard can show change between runs: `data/sample/jobs-2026-11-03.json` and `data/sample/jobs-2026-11-04.json` (the same 14 jobs a day later, with progress and costs moved on so one job gets worse, moving from WATCH to AT_RISK, and one gets better).
- Outputs per run: `output/runs/<as_of>.json` and `output/runs/index.json` (the dashboard's only inputs), `output/margin-report-<as_of>.xlsx`, `output/email/graph-sendmail-<as_of>.json`, `output/email/preview-<as_of>.html`.
- Summary flow: facts object (every number pre-formatted as a string) → model via `ModelClient` with one tool `get_job_facts(job_id)` → validator → template on any failure. Run JSON `summary` block: `text`, `source` (`ai_verified` | `template`), `provider` (`demo` | `demo-bad` | `local` | `claude` | `none`), `model`, `fallback_reason`, `rejected_tokens`.
- Interfaces: `JobSource` (`SampleFileSource` now, `SimproSource` documented only), `Mailer` (`DryRunMailer` now, `GraphMailer` documented only: Entra ID app registration, OAuth 2.0 delegated `Mail.Send`), `ModelClient` (`DemoModelClient`, `OpenAICompatibleClient`, `AnthropicClient`).
- CLI: `margin-watch run [--source PATH] [--as-of YYYY-MM-DD] [--ai demo|demo-bad|local|claude|off]`. Exit codes: 0 ok, 2 invalid input file, 1 unexpected error. A NEEDS_REVIEW job isn't an error.
- Out of scope: real Simpro, Graph or LLM calls, auth, quoting, invoicing, editing data, multi-user.

**2. `docs/acceptance-criteria.md`**: written **one phase at a time**, so every AC ID always has a test (the integrity check enforces this). Now, write the full **Phase 2** section: `AC-01`… in Given/When/Then with concrete numbers, covering every status rule below / exactly at / above each threshold, every NEEDS_REVIEW reason, main driver and ties, sort order, and both sample files' expected statuses. Then add headings for Phase 4 (outputs and CLI), Phase 5 (summary and providers) and Phase 6 (dashboard), each with a plain bullet list of the behaviours to cover later, **without AC IDs**: Excel contents and formatting, the exact Graph payload shape, the email listing only non-ON_TRACK jobs, the run JSON schema, the CLI exit codes, the validator rejecting an invented number and a re-rounded number, every fallback path, and the dashboard brief. Each later phase turns its bullets into numbered ACs before writing its tests.

**3. Sample data**: 14 fictional jobs for a Melbourne HVAC contractor (e.g. "Level 4 fit-out: VRF install", "Chiller replacement, cold-storage warehouse", "Ductwork upgrade, medical centre", "Car park exhaust fans", "Q4 preventive maintenance contract"), fictional clients and PMs only. On 4 Nov the mix is 7 ON_TRACK, 2 WATCH, 2 AT_RISK, 1 LOSS, 2 NEEDS_REVIEW (one missing percent complete, one negative actual cost), with one job exactly on a threshold. In `docs/spec.md`, a table gives each job's expected status and reason for both dates, **calculated by hand**.

**4. `docs/decisions.md`**: why the AI never does maths, why the default is a demo model, why dry-run mail, why the dashboard reads files.

Commit `docs: spec, acceptance criteria, sample data`.

---

## Phase 2: calculation tests (red)

- Set up `agent/` as a uv project: Python 3.12, package `margin_watch`. Deps: `pandas openpyxl pydantic typer httpx anthropic python-dotenv`. Dev deps: `pytest pytest-cov hypothesis ruff mypy pandas-stubs`. Script entry `margin-watch = "margin_watch.cli:app"`. Configure ruff and `mypy --strict` in `pyproject.toml`.
- Create modules with typed signatures that `raise NotImplementedError`: `models.py`, `sources.py`, `calc.py`, `status.py`, `config.py`.
- `agent/tests/conftest.py`: small explicit job builders, an autouse **socket guard**, and a fixed `AS_OF`.
- Tests for every Phase 2 AC, named `test_acNN_...` with the AC in the docstring. They include boundary tests exactly at 10%, 8 pts, 3 pts and 15%, every NEEDS_REVIEW reason, a hypothesis property (if every cost centre's forecast ≥ its estimate, forecast margin ≤ quoted margin), and a test that loads both sample files and checks every job's expected status against the spec table.
- **Red run:** `uv run pytest -q`. Every failure is NotImplementedError or an assertion.
- **Self-review** (checklist in `docs/testing-rules.md`), and fix weak tests.
- Commit `test: calculation tests (AC-xx..AC-yy)`, tag `tests-approved-2`.

## Phase 3: calculations (green)

Implement `models.py` (pydantic, Decimal), `sources.py` (`JobSource` Protocol, `SampleFileSource` with validation errors that name the job and field), `config.py` (reads `config/thresholds.toml`), `calc.py` and `status.py` (pure functions) until the Phase 2 tests pass, **without touching tests**. Run the completion gate. Coverage for calc.py and status.py must be 100%. Commit `feat: margin calculations and job status`.

---

## Phase 4: outputs and CLI (red → self-review → green)

**Red:** first turn the Phase 4 bullets into numbered ACs (continuing the numbering), then write tests for them:
- **Run JSON:** schema version, as_of, generated_at, thresholds used, counts per status, total dollars at risk, every job (all fields, cost centres, status, reason, main driver), the summary block. `runs/index.json` lists runs newest first, with counts and dollars at risk.
- **Excel (openpyxl), one workbook:**
  - "Summary": run date, counts per status, total dollars at risk.
  - "Jobs": in AC sort order. Columns Job, Client, Site, PM, Sell, Quoted margin %, Forecast margin %, Erosion (pts), Dollars at risk, Status, Main driver, Reason. AUD and % number formats, frozen header, autofilter, set column widths, and the status cell filled (red / amber / yellow / slate / green) **and** showing the status word.
  - "Cost centres": job × cost centre, estimated vs forecast, overrun %.
  - Tests open the file with openpyxl and assert the values, formats, fills, freeze panes and autofilter.
- **Graph payload**, exactly the `POST /me/sendMail` body: `{"message": {"subject", "body": {"contentType": "HTML", "content"}, "toRecipients": [{"emailAddress": {"address"}}]}, "saveToSentItems": true}`. Recipient from `config/settings.toml` (`ops@example.com`). Subject like `Margin watch, Wed 4 Nov: 1 loss, 2 at risk, 2 to review`. Body: the summary paragraph with a "Written by Demo AI · numbers verified" line (or the template label), a table of non-ON_TRACK jobs, and a footer. Simple inline-styled HTML that renders in Outlook.
- **DryRunMailer** writes the JSON and the HTML preview. A test proves no socket is opened.
- **CLI:** `--as-of` determinism (two runs with the same input are byte-identical apart from `generated_at`), exit codes 0/2/1, a readable error for a malformed file, `--ai off` uses the template.
- The email HTML and template summary are snapshot files.

Red run, self-review, then commit and tag `tests-approved-4`.

**Green:** implement `report_excel.py`, `email_graph.py`, `mailer.py`, `run.py`, `cli.py` without touching tests. Run the CLI on both sample files (`--ai off`) and list the files produced. Completion gate. Commit `feat: excel report, graph email draft, CLI`.

---

## Phase 5: summary, providers and number verification (red → self-review → green)

**Red:** first turn the Phase 5 bullets into numbered ACs, then write tests using fakes (no network):
- The facts object has every number as a pre-formatted string ("$12,480", "6.2%", "8.1 pts").
- `DemoModelClient`: first turn requests `get_job_facts` for each flagged job; after the tool results, it returns text that uses only those strings; the output is deterministic and passes validation → `ai_verified`, provider `demo`.
- `demo-bad`: the answer contains one invented number → rejected, template used, `rejected_tokens` lists it, `fallback_reason` explains.
- Text that re-rounds a number ("6%" when the fact is "6.2%") → rejected.
- The tool-use loop: an unknown `job_id` returns a tool error result, not a crash; the loop stops after at most 6 rounds.
- `AnthropicClient` with a fake SDK client: request shape (model, system, tools, max_tokens 500, temperature 0) and response parsing; no key → template, `fallback_reason: "no_api_key"`, no error.
- `OpenAICompatibleClient` with `httpx.MockTransport`: request shape for `/v1/chat/completions` with tools; unreachable or timeout → template, run still exits 0.
- Dates, job IDs and other identifiers in the facts don't trip the validator.

Red run, self-review, then commit and tag `tests-approved-5`.

**Green:**
- `ModelClient` Protocol: `complete(system, messages, tools) -> ModelTurn` (tool calls or text). One shared tool-use loop in `summarise.py` works against it.
- `DemoModelClient`: scripted and deterministic. It varies its phrasing per job with a stable hash of the job id, leads with what needs action today and names the PM, and only uses the exact strings the tool returned. `demo-bad` adds one invented figure such as "about $15,000".
- `AnthropicClient` (Anthropic Python SDK, 20 s timeout) and `OpenAICompatibleClient` (httpx, `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL`, 30 s timeout).
- System prompt in `prompts/summary_system.md`, used by every provider: writing for a busy ops manager at an HVAC contractor; plain Australian English; 3–6 sentences; lead with what needs action today and who the PM is; use numbers **exactly** as given; never calculate, round, add, compare or estimate; if a number isn't in the facts, leave it out; no greeting or sign-off.
- `validate.py`: extracts money, percentages, points, decimals and integers, and each must exactly match a string in the facts allow-list.
- Wire `--ai` and `MARGIN_WATCH_AI` (default `demo`), loading `agent/.env` if present.
- Completion gate. Commit `feat: verified summary with demo, local and Claude providers`.

---

## Phase 6: dashboard (ACs → red → self-review → green → visual review)

Create `dashboard/` with the current stable SvelteKit + TypeScript (strict) + Tailwind, `adapter-static`, Vitest, Playwright (chromium, 1 worker, 0 retries) and `@axe-core/playwright`. Run `npx playwright install chromium`. A `sync-runs` script copies `output/runs/*.json` into `dashboard/static/runs/`. No backend, no database.

**Fixtures:** a committed generator script creates `dashboard/tests/fixtures/runs/` by running the real CLI: 3 Nov with `demo-bad` (shows a rejected AI answer) and 4 Nov with `demo` (verified). Also an empty fixture set and one malformed run file. Commit the generator so the shapes can't drift.

### UI brief

A calm, trustworthy internal ops tool, not a flashy SaaS page. **The ops manager should know within 5 seconds which jobs need a phone call today.**

- **Top bar:** "Margin Watch" wordmark, the run date and time ("Run Wed 4 Nov 2026, 6:30 AM Melbourne"), a "Sample data" pill, and a run picker (newest first).
- **KPI row (4 tiles):** Jobs needing action, Dollars at risk, Average forecast margin, Jobs to review. Big tabular numbers, small labels, and one line of context comparing with the previous run ("+1 since Tue 3 Nov").
- **Summary card:** the summary in 16–17px text, max ~70 characters per line, with flagged job names as links that open the drawer. Its badge shows the provider and result: "Demo AI · numbers verified" (check icon), or "Template summary · AI answer rejected" with an expandable "Why?" that lists the rejected number(s), or "Template summary".
- **Jobs table:** risk order by default. Columns Status, Job, Client, PM, Quoted %, Forecast %, Erosion, $ at risk, Main driver. The status pill has an icon, the word and a colour (LOSS red, AT RISK amber, WATCH yellow, NEEDS REVIEW slate, ON TRACK green), never colour alone. Numbers right-aligned with tabular-nums. Sticky header, sortable columns with aria-sort, status filter chips with counts, search by job or client, an "x of 14 jobs" count. A small "↑ worse since last run" marker on jobs whose status got worse. Rows keyboard-focusable; Enter or click opens the drawer.
- **Job drawer** (from the right, `role="dialog"`, focus trapped, Esc and backdrop close it, focus returns to the row): header with job, client, site, PM and status; a "Why it's flagged" sentence; a bullet chart per cost centre (estimate bar, forecast marker, overrun highlighted, values labelled) drawn in plain SVG; quoted vs forecast margin; for NEEDS_REVIEW, the exact data problem and "What to check in Simpro".
- **States:** empty ("No runs yet. Run `margin-watch run`."), loading skeletons, an error card for a malformed run file. The page never crashes.
- **Visual design:** Inter (or the system UI font); `font-variant-numeric: tabular-nums` on all numbers; neutral slate background, white cards, 1px borders, 12px radius, shadow only on the drawer; one accent colour (deep teal) for links and focus rings, plus the status colours and nothing else; 8px spacing grid; at most 3 text sizes per card; CSS-variable tokens with a dark theme via `prefers-color-scheme`; 150–200 ms ease-out motion for the drawer and hovers only, turned off under `prefers-reduced-motion`.
- **Responsive:** designed at 1280px, works at 1024px, and at 390px the table becomes stacked cards (status, job, $ at risk, forecast %).
- **Accessibility:** WCAG AA contrast in both themes, visible focus everywhere, labelled icons, real table semantics.

**Red:**
1. Write the Phase 6 ACs in `docs/acceptance-criteria.md` from the brief.
2. Vitest tests: number formatting, status pill (icon and word), sorting and filtering logic, change-since-last-run logic, bullet-chart geometry.
3. Playwright E2E tests (rules in `docs/testing-rules.md`, at least 2 actions and an outcome each):
   - KPI values equal the latest fixture run, and the "since last run" line is right,
   - default risk order, then sort by $ at risk, then back,
   - status filter and search together, with the count updating,
   - drawer opened by mouse and by keyboard, closed with Esc, focus returning to the row, content matching the job,
   - switching to the 3 Nov run shows "AI answer rejected" and the "Why?" panel lists the invented number; switching back shows "Demo AI · numbers verified",
   - a summary job link opens the right drawer,
   - empty state, and the error state for the malformed file,
   - at 390px, cards show and the drawer still works,
   - axe: no serious or critical violations on the page and in the open drawer.
4. Red run, self-review, then commit and tag `tests-approved-6`.

**Green:** build until every test passes, without touching tests. Then do a **visual self-review**: take Playwright screenshots at 1280, 1024 and 390 px in light and dark, plus the open drawer, save them in `docs/screenshots/`, look at each one, and write down specific problems against the brief (crowding, alignment, weak hierarchy, contrast, truncation, anything that looks unfinished). Fix them and re-shoot, at least two rounds, keeping tests green. Completion gate. Commit `feat: dashboard`.

---

## Phase 7: CI, docs, demo

1. `.github/workflows/ci.yml`: on push and PR, an agent job (ruff, ruff format --check, mypy --strict, pytest with coverage, check_test_integrity) and a dashboard job (check, lint, vitest, playwright chromium), with uv and npm caching and the Playwright report uploaded on failure.
2. `Makefile`:
   - `make test`: everything in the completion gate.
   - `make demo`: clears `output/`, runs the CLI for 3 Nov with `--ai demo-bad` and 4 Nov with `--ai demo`, syncs runs, builds the dashboard, starts `vite preview` on port 4173, and prints the URL and the paths of the Excel file and email preview.
   - `make clean`.
3. `docs/scheduling.md`: a cron line and a Windows Task Scheduler XML for 6:30 AM Australia/Melbourne, logging to `output/logs/`.
4. `README.md`, written for a non-technical reader first:
   - what it does in 3 sentences, plus the 1280px screenshot,
   - "How the AI is kept honest": code does the maths, the model only writes words, every number is verified, and a rejected answer falls back to a template (with links to the validator tests),
   - "AI providers": demo (default, offline), local, Claude, and that the demo shows the real loop and validator but scripted wording,
   - "How this was built": ATDD, acceptance criteria, frozen tests and the protection hook, AC → test traceability, and the `tests-approved-*` tags,
   - quickstart (`make demo`),
   - "From prototype to production": `SimproSource` (Simpro REST API: jobs and cost centres, OAuth, webhooks to re-run on job changes), `GraphMailer` (Entra ID app registration, delegated `Mail.Send`, or application permission with admin consent for a shared mailbox), switching `MARGIN_WATCH_AI` to `claude`, and running on a schedule,
   - a "Sample data only" disclaimer.

Completion gate. Commit `docs: README, CI, scheduling, make demo`.

---

## Final phase: hand-over documents and report

Run `make demo` yourself and use the real running app, the real Excel file and the real email preview to write the two documents below. Every job name, number, button label and badge text in them must match what the app actually shows (copy them from the 4 Nov and 3 Nov runs). Use Playwright to confirm the key steps of the checklist really work before writing them down.

### `docs/manual-qa-checklist.md` (for Zeddrix to play with the demo)

- Setup: the exact commands (`make demo`), the URL, and how to stop it.
- 25–40 checkbox steps grouped by area: first impression (5-second test: which job needs a call?), KPI tiles and "since last run", summary card and badge, switching to 3 Nov to see the rejected AI answer and its "Why?", jobs table (sort, filter chips, search, counts, worse-since-last-run marker), the drawer by mouse and keyboard (Esc, focus return, bullet chart values), each NEEDS_REVIEW job and its "What to check in Simpro", the 390px phone view (browser dev tools), dark mode, the Excel report (each sheet, formats, colours), the email preview HTML and the Graph JSON, the CLI (`--ai off`, `--ai demo-bad`, a malformed file → exit code 2 and a readable error), running `make test`.
- For each step: what to do, then **Expected:** the exact thing you should see (real values).
- A "Things to say while poking around" box: 5 one-liners that explain what each part proves.
- A short "If something looks wrong" section: where the logs and outputs are, and how to re-run.

### `docs/loom-script.md` (word-for-word script, 3 minutes max)

- Written in Zeddrix's voice: plain, friendly, confident, Australian-client-friendly, no jargon without a one-line explanation. He's sending it to a hiring manager at a commercial air-conditioning contractor, who asked whether he'd built anything for quoting, scheduling, job tracking or invoicing. He hadn't, so he built this.
- Before recording: a setup checklist (run `make demo`, browser zoom 110%, close other tabs, which windows to have open and in what order, light mode).
- Sections with timings, each with **[SCREEN]** (exactly what to click or show) and **SAY:** (the exact words):
  1. Hook, about 20 s: "You asked if I've built quoting or job tracking tools. I hadn't for a business, so I built a small one with made-up data: a margin checker for jobs."
  2. Dashboard, about 60 s: the 5-second read, the KPI tiles, the LOSS job at the top; open its drawer and explain the main driver using the real numbers.
  3. The honest AI, about 40 s: the "Demo AI · numbers verified" badge; switch to 3 Nov and show the rejected answer and its invented number. Say the code does the maths, the model only writes words, and swapping the demo model for Claude is one setting.
  4. The morning output, about 25 s: the Excel report, then the email preview: "This is the Microsoft Graph sendMail body, so connecting it to Outlook is a config step, not a rewrite."
  5. How it was built, about 25 s: one AC in `acceptance-criteria.md`, the test with the same ID, the green `make test` run: "Tests are written from the acceptance criteria first and then locked, so the AI can't change them to make them pass."
  6. Close, about 10 s: "Next step for real data would be a Simpro connector. Happy to walk you and your partner through it."
- Honesty rules: say "made-up data" and "shaped like Simpro". Never say it's connected to Simpro or Outlook. Never call the demo model Claude.
- After the script: 3 likely follow-up questions from the hiring manager or their partner, with short answers.

### Final report

Update `docs/progress.md` with: total tests (unit and E2E), coverage, an AC → test table showing every AC covered, confirmation that `git diff` against every `tests-approved-*` tag shows no changes to approved tests, the list of decisions made, and any open questions. Commit `docs: manual QA checklist, Loom script, final report`.

Done when the completion gate passes, `make demo` works from a clean `output/`, and both hand-over documents are written against the real app.
