"""CLI: files written, as-of handling, determinism, exit codes (AC-46..AC-49)."""

import json

from cli_helpers import load_json, run_cli, run_sample
from openpyxl import load_workbook

FILES_4_NOV = (
    "runs/2026-11-04.json",
    "runs/index.json",
    "margin-report-2026-11-04.xlsx",
    "email/graph-sendmail-2026-11-04.json",
    "email/preview-2026-11-04.html",
)


def _no_output(out_dir):
    return not out_dir.exists() or not any(out_dir.rglob("*"))


def test_ac46_successful_run_writes_and_prints_every_file(tmp_path):
    """AC-46: exit 0, the five files exist (as-of from snapshot_date) and each path is printed."""
    result = run_sample(tmp_path)

    assert result.exit_code == 0, result.output
    for relative in FILES_4_NOV:
        assert (tmp_path / relative).is_file(), relative
        assert str(tmp_path / relative) in result.stdout, relative


def test_ac46_explicit_as_of_names_the_files(tmp_path):
    """AC-46: --as-of 2026-11-05 names the files for that date and sets as_of."""
    result = run_sample(tmp_path, extra=("--as-of", "2026-11-05"))

    assert result.exit_code == 0, result.output
    assert load_json(tmp_path / "runs" / "2026-11-05.json")["as_of"] == "2026-11-05"
    assert (tmp_path / "margin-report-2026-11-05.xlsx").is_file()
    assert (tmp_path / "email" / "graph-sendmail-2026-11-05.json").is_file()
    assert not (tmp_path / "runs" / "2026-11-04.json").exists()


def _cell_values(path):
    workbook = load_workbook(path)
    return {ws.title: list(ws.iter_rows(values_only=True)) for ws in workbook.worksheets}


def test_ac47_same_input_same_bytes(tmp_path):
    """AC-47: same file + same --generated-at -> byte-identical text outputs, same Excel values."""
    first, second = tmp_path / "a", tmp_path / "b"
    assert run_sample(first).exit_code == 0
    assert run_sample(second).exit_code == 0

    for relative in FILES_4_NOV:
        if relative.endswith(".xlsx"):
            assert _cell_values(first / relative) == _cell_values(second / relative)
        else:
            assert (first / relative).read_bytes() == (second / relative).read_bytes(), relative


def test_ac47_only_generated_at_differs(tmp_path):
    """AC-47: a different --generated-at changes only generated_at in the run JSON."""
    assert run_sample(tmp_path / "a").exit_code == 0
    assert run_sample(tmp_path / "b", generated_at="2026-11-04T07:15:00+11:00").exit_code == 0
    first = load_json(tmp_path / "a" / "runs" / "2026-11-04.json")
    second = load_json(tmp_path / "b" / "runs" / "2026-11-04.json")

    assert first.pop("generated_at") == "2026-11-04T06:30:00+11:00"
    assert second.pop("generated_at") == "2026-11-04T07:15:00+11:00"
    assert first == second


def test_ac48_missing_file_exits_2(tmp_path):
    """AC-48: a missing source file -> exit 2, readable message naming the file, no traceback."""
    out = tmp_path / "out"

    result = run_sample(out, tmp_path / "nope.json")

    assert result.exit_code == 2
    assert "Invalid input file:" in result.output
    assert "nope.json" in result.output
    assert "Traceback" not in result.output
    assert _no_output(out)


def test_ac48_not_json_exits_2(tmp_path):
    """AC-48: a file that isn't JSON -> exit 2, message names the file, no outputs."""
    source = tmp_path / "broken.json"
    source.write_text("{ not json")
    out = tmp_path / "out"

    result = run_sample(out, source)

    assert result.exit_code == 2
    assert "Invalid input file:" in result.output
    assert "broken.json" in result.output
    assert "Traceback" not in result.output
    assert _no_output(out)


def test_ac48_job_missing_field_exits_2(tmp_path):
    """AC-48: a job missing `client` -> exit 2, message names the job id and the field."""
    job = {
        "id": "2002", "name": "Job", "site": "Site", "stage": "In progress",
        "project_manager": "PM", "quoted_sell_ex_gst": "1000", "percent_complete": 50,
        "cost_centres": [{"name": "Labour", "estimated_cost": "500", "actual_cost_to_date": "0"}],
    }  # fmt: skip
    source = tmp_path / "jobs.json"
    source.write_text(json.dumps({"snapshot_date": "2026-11-04", "jobs": [job]}))
    out = tmp_path / "out"

    result = run_sample(out, source)

    assert result.exit_code == 2
    assert "Invalid input file:" in result.output
    assert "2002" in result.output
    assert "client" in result.output
    assert "Traceback" not in result.output
    assert _no_output(out)


def test_ac49_unexpected_error_exits_1(tmp_path):
    """AC-49: output dir is an existing file -> exit 1, 'Unexpected error:', no traceback."""
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("I am a file")

    result = run_sample(blocker)

    assert result.exit_code == 1
    assert "Unexpected error:" in result.output
    assert "Traceback" not in result.output


def test_ac49_bad_as_of_is_a_usage_error_not_a_crash(tmp_path):
    """AC-49: a malformed --as-of is rejected with a readable message (no traceback)."""
    result = run_cli("--as-of", "4/11/2026", "--ai", "off", "--output-dir", str(tmp_path))

    assert result.exit_code == 2
    assert "YYYY-MM-DD" in result.output
    assert "Traceback" not in result.output
