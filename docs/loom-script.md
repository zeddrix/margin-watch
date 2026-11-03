# Loom script: Margin Watch (3 minutes)

For: a hiring manager at a commercial air-conditioning contractor, who asked whether I'd built anything for quoting, scheduling, job tracking or invoicing. I hadn't for a business, so I built this.

Honesty rules for the whole recording: say **"made-up data"** and **"shaped like Simpro"**. Never say it's connected to Simpro or Outlook. Never call the demo AI "Claude".

## Before recording

- [ ] In the repo: `make test` and leave that terminal showing the last lines ("tests-approved-6: OK", "All checks passed."). Then, in a second terminal tab, run `make demo` and wait for `Dashboard: http://localhost:4173`.
- [ ] Chrome, **light mode**, browser zoom **110%**, all other tabs closed. One tab: http://localhost:4173 (on **Wed 4 Nov 2026**).
- [ ] Have open, in this order, ready to switch to:
  1. Chrome with the dashboard
  2. Excel with `output/margin-report-2026-11-04.xlsx` on the **Jobs** sheet
  3. A second Chrome tab (opened but not selected) with `output/email/preview-2026-11-04.html`
  4. VS Code with `docs/acceptance-criteria.md` scrolled to **AC-10**, and `agent/tests/test_status.py` in a split pane at `test_ac10_at_risk_below_ten_pct_forecast_margin`
  5. The terminal showing the green `make test` ending
- [ ] Notifications off. Do one practice run against a timer.

---

## 1. Hook (0:00–0:20)

**[SCREEN]** Dashboard, scrolled to the top, mouse still.

**SAY:** "Hi. You asked if I'd built anything for quoting or job tracking. I hadn't for a business, so I built a small one with made-up data: a margin checker for jobs. It's for a contractor like yours, and it takes about three minutes to show."

## 2. Dashboard (0:20–1:20)

**[SCREEN]** Move the mouse across the four KPI tiles, then to the "Call today" list on the right of the summary.

**SAY:** "Every morning it reads the jobs, 14 made-up HVAC jobs shaped like a Simpro export, and works out the margin on each one. The ops manager should know within five seconds who to ring. Three jobs need action today, up one since yesterday. Sixty-six thousand three hundred dollars is forecast over budget, and the average forecast margin is fifteen point seven percent."

**[SCREEN]** Point at the "Call today" card for 1042, then the LOSS row at the top of the table. Click the **1042** row; the drawer opens.

**SAY:** "Top of the list: the chiller replacement at the cold-storage warehouse. It was quoted at seventeen and a half percent margin, but at the current burn rate it's heading for minus two and a half: a loss."

**[SCREEN]** Point at the Labour bullet chart: the red overrun and "+50.0%".

**SAY:** "The main driver is labour. The job's sixty percent done, and at that rate labour lands at thirty-six thousand against a twenty-four thousand estimate. That's twelve thousand, or fifty percent, over. So the call is to Dave, the PM, today, not when the job closes and the profit's already gone."

**[SCREEN]** Press Esc. Point at the two NEEDS REVIEW rows.

**SAY:** "And when the data's wrong, like a missing percent complete or a negative cost, it doesn't guess. It says exactly what to check in Simpro."

## 3. The honest AI (1:20–2:00)

**[SCREEN]** Scroll up to the summary card and point at the green badge "Demo AI · numbers verified".

**SAY:** "This summary is written by AI, but the AI never does the maths. The code calculates every number, and the AI only writes the sentences around them. Then every number it writes is checked against the code's figures."

**[SCREEN]** Pick **Tue 3 Nov 2026** in the run picker. The badge turns amber: "Template summary · AI answer rejected". Click **Why?** and point at **$13,750**.

**SAY:** "On this morning the AI slipped in a number, thirteen thousand seven hundred and fifty, that the code never calculated. So the answer was thrown out automatically and a plain template went out instead. This one's a built-in demo model so it runs offline for free. Swapping it for Claude is one setting, and the same check still applies."

**[SCREEN]** Switch back to **Wed 4 Nov 2026**.

## 4. The morning output (2:00–2:25)

**[SCREEN]** Switch to Excel, Jobs sheet: the coloured Status column and the sort order.

**SAY:** "It also writes the Excel report: worst jobs first, colour-coded, ready to filter."

**[SCREEN]** Switch to the email preview tab and scroll slowly past the table of seven jobs.

**SAY:** "And it drafts the ops manager's morning email. This is the Microsoft Graph sendMail body, so connecting it to Outlook is a config step, not a rewrite. For now it's saved, never sent."

## 5. How it was built (2:25–2:50)

**[SCREEN]** VS Code: highlight **AC-10** in `acceptance-criteria.md`, then the matching `test_ac10_…` test in the split pane.

**SAY:** "Every behaviour is written down first as an acceptance criterion. This one says nine point nine nine percent is at risk and exactly ten percent isn't. The test carries the same ID."

**[SCREEN]** Switch to the terminal: "tests-approved-6: OK", "All checks passed."

**SAY:** "Tests are written from the acceptance criteria first and then locked, so the AI can't change them to make them pass. All ninety criteria have tests, and they're all green."

## 6. Close (2:50–3:00)

**[SCREEN]** Back to the dashboard on 4 Nov.

**SAY:** "The next step for real data would be a Simpro connector. Happy to walk you and your partner through it. Thanks."

---

## Likely follow-up questions

**"Is this connected to our Simpro?"**
No. It's made-up data in the same shape as a Simpro job costing export. The connector would read jobs and cost centres from Simpro's API, and could re-run whenever a job changes. The rest of the tool stays the same.

**"What if the AI gets a number wrong in front of a client?"**
It can't get through. Every number the AI writes is checked against the figures the code calculated. If even one doesn't match, the AI's answer is dropped and a plain template summary is used, and the email and dashboard say so.

**"How long would it take to make this real for us?"**
The calculations, report, email format and dashboard are done and tested. The real work is the Simpro connection, agreeing the thresholds with your ops team (for example "under 10% is at risk"), and setting up the Outlook mailbox. That's a scoped piece of work I'd be happy to estimate with you.
