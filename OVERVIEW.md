# Margin Watch: overview

Margin Watch is a small tool that checks every morning which jobs are losing money, and tells the ops manager in plain English.

## The problem it solves

An HVAC company quotes a price for each job, like "we'll install this chiller for $80,000." Partway through, labour or materials can run over budget, and nobody notices until the job is finished and the profit is gone. Margin Watch catches that early.

## What it does, step by step

1. **Reads the jobs.** It loads a file of 14 made-up HVAC jobs. Each job has a quoted price, a budget for labour, materials, subcontractors and equipment hire, what's been spent so far, and how far along the job is.
2. **Does the maths in code.** For each job it works out:
   - the profit it was quoted at,
   - the profit it's heading for at the current spending rate,
   - how much profit has slipped,
   - which cost is causing it (for example, "labour is running 34% over").
3. **Gives each job a status:**
   - 🔴 **Loss:** heading for a loss.
   - 🟠 **At risk:** profit is getting too thin.
   - 🟡 **Watch:** starting to slip.
   - ⚪ **Needs review:** the data is missing or wrong, so it won't guess.
   - 🟢 **On track.**
4. **Makes an Excel report** with all the jobs, colour-coded and sorted with the worst first.
5. **Drafts the morning email** to the ops manager, formatted the way Microsoft Outlook expects, so connecting it to Outlook later is easy. It saves the email and never sends it.
6. **Writes a short summary**, like "Job 1042 at the warehouse is heading for a loss, mostly labour. Call Dave today." The AI writes the words, but every number comes from the code. If the AI writes a number the code didn't calculate, the summary is thrown out and a plain template is used instead. That's your "the AI never does the maths" answer, working for real.
7. **Shows it all on a dashboard** in the browser: big numbers at the top, a sorted list of jobs, and a side panel with a chart for each job showing where the money is going over.

## What it doesn't do

- It doesn't connect to Simpro, Outlook or any real system. All the data is made up, just set up the way those systems are.
- It doesn't use a paid AI. A built-in demo AI follows the real process, including one deliberately bad answer so you can show it getting rejected.
- It doesn't do quoting or invoicing. It covers one part of the business: job costing and margin.

## How it's built (the part to show the hiring team)

- Every behaviour is first written down as an acceptance criterion, like "if profit drops below 10%, mark it At risk."
- Tests are written from those criteria before any code.
- The tests are then locked, so the AI building it can't change them to make them pass.
- The code is written until all the tests pass.

## What you'll end up with

- A working demo you can click through.
- A **manual QA checklist** (`docs/manual-qa-checklist.md`) so you can try it yourself and get to know it.
- A **Loom script** (`docs/loom-script.md`) for the 3-minute video you'll send the hiring manager.
