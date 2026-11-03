# Dashboard visual self-review

Screenshots in `docs/screenshots/` (taken with `dashboard/scripts/screenshots.mjs` against the committed 4 Nov fixture): 1280, 1024 and 390 px, light and dark, plus the open drawer at 1280 and 390.

## Round 1 (first build)

| # | Problem against the brief | Fix |
|---|---|---|
| 1 | **5-second test weak.** The answer to "which jobs need a phone call today?" was buried in a dense 6-sentence paragraph, and the right half of the summary card was empty at 1280. | Added a **"Call today"** list in that column: one card per LOSS / AT RISK job with the status pill, job, "$ at risk", "Call {PM}" and forecast margin, each opening the drawer. It stacks above the summary text below 1024 px, so on a phone it's the first thing after the KPIs. |
| 2 | Drawer header: "site · PM · stage" wrapped and left "progress" as an orphan line. | Site on one line, "PM … · stage" on the next. |
| 3 | Summary card used four text sizes (the "Why?" panel at 14 px). | "Why?" panel set to 13 px: three sizes per card. |
| 4 | axe (found by the E2E test): the drawer's scrolling body had no focusable element; the pressed "All" chip's count failed contrast in dark mode. | The dialog itself scrolls (it contains the close button) with a sticky header; pressed chips use the full text colour for the count. |

## Round 2

| # | Problem | Fix |
|---|---|---|
| 5 | **At 1024 px the page was 1125 px wide** (horizontal page scroll). The page grid track used `min-width: auto`, so the table's min-content width pushed the layout out and the table's own `overflow-x` never applied. | `grid-template-columns: minmax(0, 1fr)` on the page stack. |
| 6 | At 1024 px the KPI tiles dropped to 2 × 2 although 4 fit, pushing the table down. | Tiles go 2 × 2 only below 900 px. |
| 7 | At 1024 px the table still scrolled inside its card and "Main driver" was clipped. | At ≤ 1100 px: 13 px table text, a narrower job column, PM may wrap, 8 px cell padding. Measured afterwards: the table's scroll width equals its client width at 1024 (974 = 974) and 1280 (1190 = 1190); no page overflow at 390. |

## Checked and fine

- Status always shows icon + word + colour; numbers right-aligned with tabular figures; $ at risk bold.
- Dark theme: every tone pair is readable; the bullet-chart estimate/spent/forecast/overrun keys are distinct in both themes.
- 390 px: KPIs 2 × 2, "Call today" first, cards show status, job, $ at risk and forecast; drawer full-width.
- Motion: 180 ms ease-out slide/fade on the drawer and 150 ms hovers only; off under `prefers-reduced-motion`.
