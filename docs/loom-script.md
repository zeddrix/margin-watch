# Loom script: Margin Watch (3 minutes)

For: a hiring manager at a commercial air-conditioning contractor, who asked whether I'd built anything for quoting, scheduling, job tracking or invoicing. I hadn't for a business, so I built this.

Honesty rules for the whole recording: say **"made-up data"** and **"shaped like Simpro"**. Never say it's connected to Simpro or Outlook. Never call the demo AI "Claude". The Run button really runs the program; say "slowed down so you can follow it" if you mention speed.

## Before recording

- [x] In the repo: `make test` and leave that terminal showing the last lines ("tests-approved-8: OK", "All checks passed."). Then, in a second terminal tab, run `make demo` and wait for `Margin Watch is running at http://localhost:4173`.
- [x] Chrome, **light mode**, browser zoom **110%**, all other tabs closed. One tab: [http://localhost:4173](http://localhost:4173) (on **Wed 4 Nov 2026**, top of the page).
- [x] Do one practice run of the button, then press **Run it again normally** so the last run is the clean one.
- [x] Have ready, in this order: Chrome with the dashboard · VS Code with `docs/acceptance-criteria.md` at **AC-10** and `agent/tests/test_status.py` at `test_ac10_at_risk_below_ten_pct_forecast_margin` in a split pane · the terminal with the green `make test` ending.
- [x] Notifications off. One practice run of the whole script against a timer.

---



## 1. Hook (0:00–0:15)

**[SCREEN]** Dashboard, mouse still.

> **SAY:** "Hi. You asked if I'd built anything for quoting or job tracking. I hadn't for a business, so I built a small one with made-up data: a margin checker for jobs."

## 2. Press the button (0:15–0:55)

**[SCREEN]** Point at **Run this morning's check** and the "Dry run · nothing is sent" label, then click it. The panel opens and the steps tick off one by one. Don't talk over the first two seconds.

> **SAY:** "It's built to run on its own every morning at 6:30. Here I'll press the button so you can watch it. It's a dry run, so nothing gets sent."

**[SCREEN]** As each step ticks: point at the tally chips, then the two "bad data" jobs, then the green number chips.

> **SAY:** "It reads 14 made-up HVAC jobs, shaped like a Simpro export. 

It does the maths: one job heading for a loss, two at risk. 

Two jobs have missing or wrong data, so it flags them instead of guessing. 

Then the AI writes the summary, and every number in it is checked against the calculations. All green, so it's approved. 

Then it saves the Excel report and drafts the email.

Here I have the Excel sheet for the summary, jobs, and cost centres.

It's slowed down so I can demo it but this process is fast."

**[SCREEN]** "Done. Nothing was sent." Click **See the results**.

## 3. What it found (0:55–1:35)

**[SCREEN]** Point at the four KPI tiles, then the **Call today** list.

> **SAY:** "So: three jobs need a call today, and **$66,300** is forecast over budget. The ops manager knows in five seconds who to ring."

**[SCREEN]** Click the **1042** row. The drawer opens. Point at the Labour chart: the red overrun, "+50.0%".

> **SAY:** "Top of the list is the chiller replacement at the cold-storage warehouse. It was quoted at seventeen and a half percent margin, but at the current spending rate it's heading for minus two and a half: a loss. The cause is labour: thirty-six thousand forecast against a twenty-four thousand estimate. So the call to Dave, the PM, happens today, not when the job closes."

**[SCREEN]** Press Esc.

## 4. The honest AI, live (1:35–2:15)

**[SCREEN]** Click **Run this morning's check** again. When it finishes, click **Try it with a made-up AI number**. Point at the red chip **"$13,750 not in the calculations"** and the orange step.

> **SAY:** "Here's the part I care about most. The AI never does the maths: the code calculates every number, and the AI only writes the words. Watch what happens when I make the AI slip in a number of its own. 

Thirteen thousand seven hundred and fifty: not in the calculations, so the whole answer is rejected and a plain, safe summary goes out instead. This one's a built-in demo AI that runs offline for free. Switching it to Claude is one setting, and the same check still applies."

**[SCREEN]** Click **Run it again normally**, wait for "Done", then click **Preview email**. The email opens in a new tab.

## 5. The morning output (2:15–2:35)

**[SCREEN]** Scroll the email preview slowly past the table of seven jobs, then switch back to the dashboard tab.

> **SAY:** "This is the morning email it drafts, in the format Microsoft's Outlook system expects, so connecting it to Outlook later is a config step, not a rewrite. It also saves the Excel report, worst jobs first."

## 6. How it was built (2:35–2:52)

**[SCREEN]** VS Code: highlight **AC-10**, then the matching `test_ac10_…` test. Switch to the terminal: "All checks passed."

> **SAY:** "Every behaviour is written down first, like 'under ten percent margin is at risk', then tested. The tests are locked so the AI that built it can't change them to pass, and they're all green."

## 7. Close (2:52–3:00)

**[SCREEN]** Back to the dashboard, scrolled to the top so the KPI tiles and the "Call today" list are in view. Hold still for two seconds after the last word, then stop recording.

> **SAY:** "So that's Margin Watch: one button, the maths done in code, every number the AI writes checked, and a clear list of who to call each morning. Thanks for watching."

---



## Likely follow-up questions

**"Is this connected to our Simpro?"**
No. It's made-up data in the same shape as a Simpro job costing export. The connector would read jobs and cost centres from Simpro's API, and could re-run whenever a job changes. The rest of the tool stays the same.

**"What if the AI gets a number wrong in front of a client?"**
It can't get through. Every number the AI writes is checked against the figures the code calculated. If even one doesn't match, the answer is dropped and a plain template summary is used, and the email and dashboard say so. You saw that happen live with the $13,750.

**"How long would it take to make this real for us?"**
The calculations, report, email format and dashboard are done and tested. What's left is connecting it to the real job data, agreeing the thresholds with the ops team (for example "under 10% is at risk"), and setting up the Outlook mailbox.