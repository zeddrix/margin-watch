# Manual QA checklist: play with the demo

About 20 minutes. Every value below is what the app showed when this checklist was written (from `make demo`). All data is made up.

## Setup

```bash
cd ~/Documents/margin-watch
make demo
```

- Wait for `Dashboard: http://localhost:4173` in the terminal, then open **http://localhost:4173** in Chrome.
- The terminal also prints the paths of the Excel report, the email preview and the Graph payload.
- **To stop:** press **Ctrl+C** in that terminal.
- To start again from scratch: `make clean` then `make demo`.

## 1. First impression (the 5-second test)

- [ ] Open the page and look for 5 seconds. Which job needs a phone call?
  **Expected:** the "Call today" list on the right of the summary shows **LOSS $16,000 at risk · 1042 Chiller replacement, cold-storage warehouse · Call Dave Kowalski · forecast -2.5%**, then 1038 (Priya Nair, $23,000) and 1035 (Sam Okafor, $14,000).
- [ ] Look at the top bar.
  **Expected:** "Margin Watch", a "Sample data" pill, `Run Wed 4 Nov 2026, 6:30 AM Melbourne` and a run picker set to "Wed 4 Nov 2026".

## 2. KPI tiles and "since last run"

- [ ] Read the four tiles.
  **Expected:** Jobs needing action **3** (red), "+1 since Tue 3 Nov" · Dollars at risk **$66,300**, "+$7,500 since Tue 3 Nov" · Average forecast margin **15.7%**, "-0.6 pts since Tue 3 Nov" · Jobs to review **2**, "No change since Tue 3 Nov".
- [ ] Pick **Tue 3 Nov 2026** in the run picker.
  **Expected:** the stamp changes to `Run Tue 3 Nov 2026, 6:30 AM Melbourne`; the tiles read **2 / $58,800 / 16.3% / 2**, each with "First run" (there's nothing earlier to compare with).

## 3. Summary card and badge (4 Nov)

- [ ] Pick **Wed 4 Nov 2026** again and read the badge.
  **Expected:** green **"Demo AI · numbers verified"** with a tick. It never says Claude.
- [ ] Read the first sentence.
  **Expected:** "Dave Kowalski needs a call today about Chiller replacement, cold-storage warehouse (1042), which is heading for a loss at -2.5% forecast margin against 17.5% quoted, mostly from Labour running $12,000 over estimate."
- [ ] Check every number in the summary against the jobs table.
  **Expected:** they all match exactly ($12,000, 10.8%, $18,000, 8.8%, $10,000, $66,300, …). The AI only quoted them.
- [ ] Click the underlined **Level 4 fit-out: VRF install** link.
  **Expected:** the drawer opens on "1038 Level 4 fit-out: VRF install". Press Esc and focus returns to the link.

## 4. The rejected AI answer (3 Nov)

- [ ] Pick **Tue 3 Nov 2026**.
  **Expected:** amber badge **"Template summary · AI answer rejected"**, and the text starts "Of 14 jobs, 1 is heading for a loss, 1 is at risk, 4 are on watch, 2 need a data check and 6 are on track. Forecast overruns add up to $58,800."
- [ ] Click **Why?**
  **Expected:** "The AI answer included a number the code never calculated, so it was thrown out and this template summary was used instead." and **Rejected: $13,750**.
- [ ] Pick **Wed 4 Nov 2026** again.
  **Expected:** the badge is back to "Demo AI · numbers verified" and there's no "Why?".

## 5. Jobs table

- [ ] Look at the order.
  **Expected:** worst first: 1042 LOSS, 1038 AT RISK, 1035 AT RISK, 1033 WATCH, 1040 WATCH, 1039 NEEDS REVIEW, 1044 NEEDS REVIEW, then the 7 ON TRACK jobs (1037 first, at $5,000).
- [ ] Find the marker under 1038's status.
  **Expected:** "↑ worse since last run" (it was WATCH on 3 Nov). No other job has it.
- [ ] Click the **$ at risk** header.
  **Expected:** 1038 ($23,000) jumps to the top, then 1042, 1035, 1033. The header's arrow points down.
- [ ] Click **Status**.
  **Expected:** back to the risk order.
- [ ] Click the **At risk 2** chip.
  **Expected:** only 1038 and 1035; the count reads "2 of 14 jobs".
- [ ] Type **medical** in the search box.
  **Expected:** only 1035 Ductwork upgrade, medical centre; "1 of 14 jobs". Clear the search and click **All 14**: "14 of 14 jobs" again.
- [ ] Look at 1040 Car park exhaust fans.
  **Expected:** WATCH with erosion only 0.5 pts. Equipment hire is exactly 15.0% over, which is on the threshold, so it counts.

## 6. The job drawer

- [ ] Click the **1042** row.
  **Expected:** a panel slides in from the right: "Frostline Logistics", "1042 Chiller replacement, cold-storage warehouse", "Frostline cold store, Dandenong South", "PM Dave Kowalski · In progress", a LOSS pill, and under "Why it's flagged": "Heading for a loss: forecast margin -2.5% against 17.5% quoted. Main driver: Labour, projected $12,000 (50.0%) over estimate."
- [ ] Read the four figures.
  **Expected:** Quoted margin 17.5% · Forecast margin -2.5% · Erosion 20.0 pts · Dollars at risk $16,000, and "Sell $80,000 ex GST · 60.0% complete".
- [ ] Read the Labour bullet chart.
  **Expected:** "+50.0%" in red, a red overrun segment past the estimate bar, and "Forecast $36,000 · Estimate $24,000 · Spent $21,600". Materials +10.0%, Subcontractors 0.0%, Equipment hire +25.0%.
- [ ] Press **Esc**.
  **Expected:** the drawer closes and the 1042 row has a teal focus ring.
- [ ] Keyboard only: press **Tab** until a row is focused (or click 1038 once and Esc), then press **Enter**.
  **Expected:** the drawer opens. Tab keeps cycling inside it and never reaches the page behind. Esc closes it and focus returns to the row.
- [ ] Open any drawer and click the dimmed page on the left.
  **Expected:** the drawer closes.

## 7. NEEDS REVIEW jobs

- [ ] Open **1039 Q4 preventive maintenance contract**.
  **Expected:** "Data problem: Percent complete is missing, so the forecast can't be worked out." and "The job wasn't assessed, so no margin figures are shown. Nothing is guessed." Under **What to check in Simpro**: "Ask the PM for the job's percent complete and update it in Simpro." The cost centres show estimate and spent, with forecast "—".
- [ ] Open **1044 Cooling tower water treatment upgrade**.
  **Expected:** "Materials actual cost to date is negative (-$1,250)." and "Look for a credit or reversal posted to the wrong job or cost centre in Simpro."

## 8. Phone view (390px)

- [ ] Chrome DevTools (Cmd+Opt+I) → device toolbar (Cmd+Shift+M) → width **390**.
  **Expected:** no sideways scrolling; KPI tiles 2 × 2; "Call today" sits above the summary text; the table is replaced by cards (status, "1042 Chiller replacement, cold-storage warehouse", "At risk $16,000", "Forecast -2.5%").
- [ ] Tap the 1042 card.
  **Expected:** the drawer fills the screen; the close button (×) and Esc both close it.

## 9. Dark mode

- [ ] macOS System Settings → Appearance → **Dark**, then look at the page (no reload needed).
  **Expected:** dark slate background, all text readable, status pills still distinct (red, amber, yellow, slate, green), teal links and focus rings.

## 10. Excel report

- [ ] Open `output/margin-report-2026-11-04.xlsx`.
  **Expected:** three sheets: Summary, Jobs, Cost centres.
- [ ] **Summary** sheet.
  **Expected:** "Margin Watch report", the sample-data note, Run date Wed 4 Nov 2026, Loss 1 / At risk 2 / Watch 2 / Needs review 2 / On track 7, Total jobs 14, Jobs needing action 3, Total dollars at risk $66,300.00, Average forecast margin 15.7%, the summary text, and Written by "Written by Demo AI · numbers verified".
- [ ] **Jobs** sheet.
  **Expected:** 14 rows in risk order; a frozen header with filter arrows; Sell and Dollars at risk as $ (for example $80,000.00 and $16,000.00), margins as % (17.5%, -2.5%); the Status cell filled red / amber / yellow / slate / green *and* showing the word (LOSS, AT RISK, …); 1039 and 1044 with blank margin cells.
- [ ] **Cost centres** sheet.
  **Expected:** 49 rows; the first is 1042 Labour: $24,000.00 / $21,600.00 / $36,000.00 / $12,000.00 / 50.0%.

## 11. Email draft

- [ ] Open `output/email/preview-2026-11-04.html` in the browser.
  **Expected:** "Margin watch · Wed 4 Nov 2026", the summary, "Written by Demo AI · numbers verified", and a table of the **7** jobs that aren't on track (no ON TRACK rows), then a footer: "Generated by margin-watch at 6:30 AM on Wed 4 Nov 2026 (Melbourne time) …" and "Sample data only … Dry run: this email was saved, not sent." (In `preview-2026-11-03.html` the label reads "Template summary · AI answer rejected".)
- [ ] Open `output/email/graph-sendmail-2026-11-04.json`.
  **Expected:** `{"message": {"subject": "Margin watch, Wed 4 Nov: 1 loss, 2 at risk, 2 to review", "body": {"contentType": "HTML", …}, "toRecipients": [{"emailAddress": {"address": "ops@example.com"}}]}, "saveToSentItems": true}`: exactly the body of Microsoft Graph's `POST /me/sendMail`.

## 12. Command line

Run these from the `agent/` folder in a second terminal.

- [ ] `uv run margin-watch run --source ../data/sample/jobs-2026-11-04.json --ai off --output-dir /tmp/mw-off`
  **Expected:** exit 0, "Margin watch run for Wed 4 Nov 2026 (sample data): 1 loss, 2 at risk, 2 watch, 2 to review, 7 on track.", "Summary: Template summary", then five file paths.
- [ ] `uv run margin-watch run --source ../data/sample/jobs-2026-11-04.json --ai demo-bad --output-dir /tmp/mw-bad`
  **Expected:** "Summary: Template summary · AI answer rejected".
- [ ] `echo '{ broken' > /tmp/broken.json && uv run margin-watch run --source /tmp/broken.json; echo "exit=$?"`
  **Expected:** `Invalid input file: broken.json: not valid JSON (line 1, column 3)` and `exit=2`, with no traceback.
- [ ] `uv run margin-watch run --ai claude --output-dir /tmp/mw-claude` (with no API key set)
  **Expected:** exit 0 and "Summary: Template summary"; the run JSON records `"fallback_reason": "no_api_key"`. Nothing was sent anywhere.

## 13. The tests

- [ ] Stop the demo (Ctrl+C), then from the repo root run `make test`.
  **Expected:** a few minutes of output ending with "Test integrity OK (31 test files, 90 ACs covered)", "tests-approved-2: OK" … "tests-approved-6: OK" and **"All checks passed."**

> **Things to say while poking around**
> 1. "The maths is done in code. The AI only writes sentences around numbers it's given."
> 2. "If the AI makes up a number, like that $13,750, the answer is thrown out and you get the plain template instead."
> 3. "Bad data isn't guessed: those two jobs say exactly what to fix in Simpro."
> 4. "The email is already in Outlook's Graph format, so connecting it later is configuration, not a rewrite."
> 5. "Every behaviour has an acceptance criterion and a locked test; the AI that built it couldn't change the tests to pass."

## If something looks wrong

- **Outputs:** `output/runs/` (run JSON + index), `output/margin-report-*.xlsx`, `output/email/`.
- **Re-run:** `make clean && make demo`.
- **Port 4173 busy:** another demo is running. Stop it with Ctrl+C, or run `make demo PORT=4180`.
- **"No runs yet" page:** the build has no run files. Stop the demo and run `make demo` again: it runs the CLI, copies `output/runs/` into the dashboard (`npm run sync-runs`) and rebuilds before serving.
- **Logs:** the CLI prints to the terminal; scheduled runs log to `output/logs/` (see `docs/scheduling.md`).
