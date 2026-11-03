"""The Excel report: Summary, Jobs and Cost centres sheets (openpyxl).

Percent cells hold fractions (0.175) with a `0.0%` format, as Excel expects. Money keeps cents.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

from margin_watch.calc import HUNDRED
from margin_watch.labels import STATUS_WORDS, summary_label
from margin_watch.models import STATUS_ORDER, RunReport, Status

CellValue = str | int | Decimal | date | None

AUD = '"$"#,##0.00'
PCT = "0.0%"
PTS = "0.0"
DATE = "ddd d mmm yyyy"
STATUS_FILLS: dict[Status, str] = {
    Status.LOSS: "FCA5A5",
    Status.AT_RISK: "FDBA74",
    Status.WATCH: "FEF08A",
    Status.NEEDS_REVIEW: "CBD5E1",
    Status.ON_TRACK: "86EFAC",
}
_STATUS_LABELS = {
    Status.LOSS: "Loss",
    Status.AT_RISK: "At risk",
    Status.WATCH: "Watch",
    Status.NEEDS_REVIEW: "Needs review",
    Status.ON_TRACK: "On track",
}
_JOB_COLUMNS: tuple[tuple[str, int], ...] = (
    ("Job", 46), ("Client", 28), ("Site", 36), ("PM", 16), ("Sell", 14),
    ("Quoted margin %", 12), ("Forecast margin %", 12), ("Erosion (pts)", 11),
    ("Dollars at risk", 14), ("Status", 15), ("Main driver", 16), ("Reason", 90),
)  # fmt: skip
_CENTRE_COLUMNS: tuple[tuple[str, int], ...] = (
    ("Job", 46), ("Cost centre", 18), ("Estimated", 14), ("Actual to date", 14),
    ("Forecast at completion", 22), ("Overrun ($)", 14), ("Overrun %", 12),
)  # fmt: skip


def _cents(value: Decimal | None) -> Decimal | None:
    return None if value is None else value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _fraction(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return (value / HUNDRED).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _header(ws: Worksheet, columns: Sequence[tuple[str, int]]) -> None:
    for index, (title, width) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=index, value=title)
        cell.font = Font(bold=True)
        ws.column_dimensions[cell.column_letter].width = width
    ws.freeze_panes = "A2"


def _put(ws: Worksheet, row: int, column: int, value: CellValue, number_format: str = "") -> Cell:
    cell = ws.cell(row=row, column=column, value=value)
    if number_format:
        cell.number_format = number_format
    return cell


def _summary_sheet(ws: Worksheet, report: RunReport) -> None:
    ws.title = "Summary"
    ws["A1"] = "Margin Watch report"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = "Sample data only: fictional jobs shaped like a Simpro job costing export."
    portfolio = report.portfolio
    rows: list[tuple[str, CellValue, str]] = [
        ("Run date", report.as_of, DATE),
        ("Source", report.source_name, ""),
        *[(_STATUS_LABELS[s], portfolio.counts[s], "") for s in STATUS_ORDER],
        ("Total jobs", portfolio.total_jobs, ""),
        ("Jobs needing action", portfolio.jobs_needing_action, ""),
        ("Total dollars at risk", _cents(portfolio.total_dollars_at_risk), AUD),
        ("Average forecast margin", _fraction(portfolio.average_forecast_margin_pct), PCT),
        ("Summary", report.summary.text, ""),
        ("Written by", summary_label(report.summary), ""),
    ]
    for offset, (label, value, number_format) in enumerate(rows):
        row = 4 + offset
        ws.cell(row=row, column=1, value=label).font = Font(bold=True)
        cell = _put(ws, row, 2, value, number_format)
        cell.alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 100


def _jobs_sheet(ws: Worksheet, report: RunReport) -> None:
    _header(ws, _JOB_COLUMNS)
    for row, assessment in enumerate(report.assessments, start=2):
        job = assessment.job
        metrics = assessment.metrics
        _put(ws, row, 1, f"{job.id} {job.name}")
        _put(ws, row, 2, job.client)
        _put(ws, row, 3, job.site)
        _put(ws, row, 4, job.project_manager)
        _put(ws, row, 5, _cents(job.quoted_sell_ex_gst), AUD)
        _put(ws, row, 6, _fraction(metrics.quoted_margin_pct) if metrics else None, PCT)
        _put(ws, row, 7, _fraction(metrics.forecast_margin_pct) if metrics else None, PCT)
        erosion = metrics.margin_erosion_pts.quantize(Decimal("0.0001")) if metrics else None
        _put(ws, row, 8, erosion, PTS)
        _put(ws, row, 9, _cents(metrics.dollars_at_risk) if metrics else None, AUD)
        status = _put(ws, row, 10, STATUS_WORDS[assessment.status])
        status.fill = PatternFill(fill_type="solid", fgColor=STATUS_FILLS[assessment.status])
        status.font = Font(bold=True)
        _put(ws, row, 11, assessment.main_driver)
        reason = _put(ws, row, 12, assessment.reason)
        reason.alignment = Alignment(wrap_text=True, vertical="top")
    ws.auto_filter.ref = f"A1:L{len(report.assessments) + 1}"


def _centres_sheet(ws: Worksheet, report: RunReport) -> None:
    _header(ws, _CENTRE_COLUMNS)
    row = 2
    for assessment in report.assessments:
        job = assessment.job
        results = {} if assessment.metrics is None else {
            c.name: c for c in assessment.metrics.cost_centres
        }  # fmt: skip
        for centre in job.cost_centres:
            result = results.get(centre.name)
            _put(ws, row, 1, f"{job.id} {job.name}")
            _put(ws, row, 2, centre.name)
            _put(ws, row, 3, _cents(centre.estimated_cost), AUD)
            _put(ws, row, 4, _cents(centre.actual_cost_to_date), AUD)
            _put(ws, row, 5, _cents(result.forecast_at_completion) if result else None, AUD)
            _put(ws, row, 6, _cents(result.overrun_dollars) if result else None, AUD)
            _put(ws, row, 7, _fraction(result.overrun_pct) if result else None, PCT)
            row += 1
    ws.auto_filter.ref = f"A1:G{row - 1}"


def write_excel(report: RunReport, path: Path) -> Path:
    workbook = Workbook()
    _summary_sheet(workbook.active, report)  # type: ignore[arg-type]
    _jobs_sheet(workbook.create_sheet("Jobs"), report)
    _centres_sheet(workbook.create_sheet("Cost centres"), report)
    # Fixed document timestamps keep the workbook's metadata reproducible for a given run.
    stamp = report.generated_at.replace(tzinfo=None)
    workbook.properties.created = stamp
    workbook.properties.modified = stamp
    workbook.properties.creator = "margin-watch"
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    return path
