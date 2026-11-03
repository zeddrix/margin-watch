"""Excel report contents and formatting, read back with openpyxl (AC-37..AC-40)."""

from datetime import date, datetime

import pytest
from cli_helpers import run_sample, snapshot
from openpyxl import load_workbook

AUD = '"$"#,##0.00'
PCT = "0.0%"
LOSS_1042 = (
    "Heading for a loss: forecast margin -2.5% against 17.5% quoted. "
    "Main driver: Labour, projected $12,000 (50.0%) over estimate."
)


def _workbook(tmp_path):
    result = run_sample(tmp_path)
    assert result.exit_code == 0, result.output
    return load_workbook(tmp_path / "margin-report-2026-11-04.xlsx")


def _row_values(ws, row):
    return [cell.value for cell in ws[row]]


def test_ac37_summary_sheet(tmp_path):
    """AC-37: sheet names, Summary labels -> values and formats, sample-data note."""
    wb = _workbook(tmp_path)
    ws = wb["Summary"]
    cells = {row[0].value: row[1] for row in ws.iter_rows(min_row=2) if row[0].value}

    assert wb.sheetnames == ["Summary", "Jobs", "Cost centres"]
    assert ws["A1"].value == "Margin Watch report"
    assert any("Sample data" in str(c.value) for row in ws.iter_rows() for c in row if c.value)
    assert isinstance(cells["Run date"].value, datetime)  # openpyxl reads dates back as datetimes
    assert cells["Run date"].value.date() == date(2026, 11, 4)
    assert cells["Run date"].number_format == "ddd d mmm yyyy"
    assert cells["Source"].value == "jobs-2026-11-04.json"
    counts = {k: cells[k].value for k in ("Loss", "At risk", "Watch", "Needs review", "On track")}
    assert counts == {"Loss": 1, "At risk": 2, "Watch": 2, "Needs review": 2, "On track": 7}
    assert cells["Total jobs"].value == 14
    assert cells["Jobs needing action"].value == 3
    assert cells["Total dollars at risk"].value == 66300
    assert cells["Total dollars at risk"].number_format == AUD
    assert cells["Average forecast margin"].value == pytest.approx(0.157394, abs=1e-9)
    assert cells["Average forecast margin"].number_format == PCT
    assert cells["Summary"].value == snapshot("template-summary-2026-11-04.txt").rstrip("\n")
    assert cells["Written by"].value == "Template summary"


def test_ac38_jobs_sheet_values(tmp_path):
    """AC-38: Jobs headers, risk order, the 1042 row and the NEEDS_REVIEW 1039 row."""
    ws = _workbook(tmp_path)["Jobs"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))

    assert _row_values(ws, 1) == [
        "Job", "Client", "Site", "PM", "Sell", "Quoted margin %", "Forecast margin %",
        "Erosion (pts)", "Dollars at risk", "Status", "Main driver", "Reason",
    ]  # fmt: skip
    assert len(rows) == 14
    assert [r[0].split(" ")[0] for r in rows] == [
        "1042", "1038", "1035", "1033", "1040", "1039", "1044",
        "1037", "1031", "1032", "1034", "1036", "1041", "1043",
    ]  # fmt: skip
    first = rows[0]
    assert first[:5] == (
        "1042 Chiller replacement, cold-storage warehouse",
        "Frostline Logistics",
        "Frostline cold store, Dandenong South",
        "Dave Kowalski",
        80000,
    )
    assert first[5] == pytest.approx(0.175)
    assert first[6] == pytest.approx(-0.025)
    assert first[7] == pytest.approx(20)
    assert first[8:] == (16000, "LOSS", "Labour", LOSS_1042)
    review = next(r for r in rows if r[0].startswith("1039"))
    assert review[4] == 48000
    assert review[5:9] == (None, None, None, None)
    assert review[9:] == (
        "NEEDS REVIEW",
        None,
        "Percent complete is missing, so the forecast can't be worked out.",
    )
    assert {r[9] for r in rows} == {"LOSS", "AT RISK", "WATCH", "NEEDS REVIEW", "ON TRACK"}


def test_ac39_jobs_sheet_formatting(tmp_path):
    """AC-39: number formats, freeze panes, autofilter, bold header, widths, wrap, status fills."""
    ws = _workbook(tmp_path)["Jobs"]

    assert ws["E2"].number_format == AUD
    assert ws["I2"].number_format == AUD
    assert ws["F2"].number_format == PCT
    assert ws["G2"].number_format == PCT
    assert ws["H2"].number_format == "0.0"
    assert ws.freeze_panes == "A2"
    assert ws.auto_filter.ref == "A1:L15"
    assert all(cell.font.bold for cell in ws[1])
    widths = {col: ws.column_dimensions[col].width for col in "ABCDEFGHIJKL"}
    assert widths == {
        "A": 46, "B": 28, "C": 36, "D": 16, "E": 14, "F": 12,
        "G": 12, "H": 11, "I": 14, "J": 15, "K": 16, "L": 90,
    }  # fmt: skip
    assert ws["L2"].alignment.wrap_text is True
    fills = {"LOSS": "FCA5A5", "AT RISK": "FDBA74", "WATCH": "FEF08A",
             "NEEDS REVIEW": "CBD5E1", "ON TRACK": "86EFAC"}  # fmt: skip
    for row in range(2, 16):
        cell = ws.cell(row=row, column=10)
        assert cell.fill.fill_type == "solid", cell.value
        assert cell.fill.fgColor.rgb.endswith(fills[cell.value]), cell.value


def test_ac40_cost_centres_sheet(tmp_path):
    """AC-40: one row per cost centre in risk order, formats, freeze panes, autofilter."""
    ws = _workbook(tmp_path)["Cost centres"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))

    assert _row_values(ws, 1) == [
        "Job", "Cost centre", "Estimated", "Actual to date", "Forecast at completion",
        "Overrun ($)", "Overrun %",
    ]  # fmt: skip
    assert len(rows) == 49
    assert rows[0][:6] == (
        "1042 Chiller replacement, cold-storage warehouse", "Labour", 24000, 21600, 36000, 12000,
    )  # fmt: skip
    assert rows[0][6] == pytest.approx(0.5)
    assert [r[1] for r in rows[:4]] == ["Labour", "Materials", "Subcontractors", "Equipment hire"]
    review = [r for r in rows if r[0].startswith("1039")]
    assert [r[1] for r in review] == ["Labour", "Materials"]
    assert review[0][2:4] == (30000, 12000)
    assert all(r[4:] == (None, None, None) for r in review)
    for col in "CDEF":
        assert ws[f"{col}2"].number_format == AUD
    assert ws["G2"].number_format == PCT
    assert ws.freeze_panes == "A2"
    assert ws.auto_filter.ref == "A1:G50"
