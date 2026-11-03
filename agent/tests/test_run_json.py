"""Run JSON, run index, --ai off summary block, NEEDS_REVIEW-only runs (AC-34..36, AC-50, AC-51)."""

import json

from cli_helpers import load_json, run_sample, snapshot
from conftest import SAMPLE_3_NOV

LOSS_1042 = (
    "Heading for a loss: forecast margin -2.5% against 17.5% quoted. "
    "Main driver: Labour, projected $12,000 (50.0%) over estimate."
)


def _run_4_nov(tmp_path):
    result = run_sample(tmp_path)
    assert result.exit_code == 0, result.output
    return load_json(tmp_path / "runs" / "2026-11-04.json")


def test_ac34_run_json_top_level(tmp_path):
    """AC-34: exact top-level keys and values for the 4 Nov run."""
    doc = _run_4_nov(tmp_path)

    assert set(doc) == {
        "schema_version", "as_of", "generated_at", "source", "thresholds", "counts",
        "portfolio", "jobs", "summary",
    }  # fmt: skip
    assert doc["schema_version"] == 1
    assert doc["as_of"] == "2026-11-04"
    assert doc["generated_at"] == "2026-11-04T06:30:00+11:00"
    assert doc["source"] == {"kind": "sample_file", "name": "jobs-2026-11-04.json",
                             "sample_data": True}  # fmt: skip
    assert doc["thresholds"] == {
        "at_risk_margin_pct": 10.0, "at_risk_erosion_pts": 8.0,
        "watch_erosion_pts": 3.0, "watch_overrun_pct": 15.0,
    }  # fmt: skip
    assert doc["counts"] == {"LOSS": 1, "AT_RISK": 2, "WATCH": 2, "NEEDS_REVIEW": 2,
                             "ON_TRACK": 7}  # fmt: skip
    assert doc["portfolio"] == {
        "total_jobs": 14, "jobs_needing_action": 3, "jobs_to_review": 2,
        "total_dollars_at_risk": 66300.0, "average_forecast_margin_pct": 15.7394,
    }  # fmt: skip


def test_ac35_jobs_in_risk_order_with_all_fields(tmp_path):
    """AC-35: jobs in risk order, each with every field and cost-centre field."""
    jobs = _run_4_nov(tmp_path)["jobs"]

    assert [j["id"] for j in jobs] == [
        "1042", "1038", "1035", "1033", "1040", "1039", "1044",
        "1037", "1031", "1032", "1034", "1036", "1041", "1043",
    ]  # fmt: skip
    for job in jobs:
        assert set(job) == {
            "id", "name", "client", "site", "stage", "project_manager", "quoted_sell_ex_gst",
            "percent_complete", "status", "reason", "review_code", "main_driver",
            "estimated_total", "forecast_total", "quoted_margin_pct", "forecast_margin_pct",
            "margin_erosion_pts", "dollars_at_risk", "cost_centres",
        }  # fmt: skip
        for centre in job["cost_centres"]:
            assert set(centre) == {
                "name", "estimated_cost", "actual_cost_to_date", "forecast_at_completion",
                "overrun_dollars", "overrun_pct", "estimated_hours", "actual_hours",
                "hourly_rate",
            }  # fmt: skip


def test_ac35_job_1042_entry(tmp_path):
    """AC-35: job 1042's full entry, with numbers rounded for transport."""
    job = _run_4_nov(tmp_path)["jobs"][0]

    def centre(name, est, act, fc, over, pct, hours=(None, None, None)):
        return {
            "name": name, "estimated_cost": est, "actual_cost_to_date": act,
            "forecast_at_completion": fc, "overrun_dollars": over, "overrun_pct": pct,
            "estimated_hours": hours[0], "actual_hours": hours[1], "hourly_rate": hours[2],
        }  # fmt: skip

    assert job == {
        "id": "1042",
        "name": "Chiller replacement, cold-storage warehouse",
        "client": "Frostline Logistics",
        "site": "Frostline cold store, Dandenong South",
        "stage": "In progress",
        "project_manager": "Dave Kowalski",
        "quoted_sell_ex_gst": 80000.0,
        "percent_complete": 60.0,
        "status": "LOSS",
        "reason": LOSS_1042,
        "review_code": None,
        "main_driver": "Labour",
        "estimated_total": 66000.0,
        "forecast_total": 82000.0,
        "quoted_margin_pct": 17.5,
        "forecast_margin_pct": -2.5,
        "margin_erosion_pts": 20.0,
        "dollars_at_risk": 16000.0,
        "cost_centres": [
            centre("Labour", 24000.0, 21600.0, 36000.0, 12000.0, 50.0, (240.0, 216.0, 100.0)),
            centre("Materials", 30000.0, 19800.0, 33000.0, 3000.0, 10.0),
            centre("Subcontractors", 8000.0, 4800.0, 8000.0, 0.0, 0.0),
            centre("Equipment hire", 4000.0, 3000.0, 5000.0, 1000.0, 25.0),
        ],
    }


def test_ac35_needs_review_job_has_nulls_not_guesses(tmp_path):
    """AC-35: NEEDS_REVIEW job 1039 has null computed fields and keeps its raw costs."""
    job = next(j for j in _run_4_nov(tmp_path)["jobs"] if j["id"] == "1039")

    assert job["status"] == "NEEDS_REVIEW"
    assert job["percent_complete"] is None
    assert job["review_code"] == "missing_percent_complete"
    assert job["main_driver"] is None
    for field in ("estimated_total", "forecast_total", "quoted_margin_pct",
                  "forecast_margin_pct", "margin_erosion_pts", "dollars_at_risk"):  # fmt: skip
        assert job[field] is None, field
    labour = job["cost_centres"][0]
    assert labour["name"] == "Labour"
    assert labour["estimated_cost"] == 30000.0
    assert labour["actual_cost_to_date"] == 12000.0
    for centre in job["cost_centres"]:
        assert centre["forecast_at_completion"] is None
        assert centre["overrun_dollars"] is None
        assert centre["overrun_pct"] is None


def test_ac36_index_newest_first_and_rerun_replaces(tmp_path):
    """AC-36: index lists 4 Nov then 3 Nov; re-running 3 Nov keeps exactly 2 entries."""
    assert (
        run_sample(tmp_path, SAMPLE_3_NOV, generated_at="2026-11-03T06:30:00+11:00").exit_code == 0
    )
    assert run_sample(tmp_path).exit_code == 0

    index = load_json(tmp_path / "runs" / "index.json")

    assert index["schema_version"] == 1
    assert [r["as_of"] for r in index["runs"]] == ["2026-11-04", "2026-11-03"]
    assert index["runs"][0] == {
        "as_of": "2026-11-04",
        "file": "2026-11-04.json",
        "generated_at": "2026-11-04T06:30:00+11:00",
        "counts": {"LOSS": 1, "AT_RISK": 2, "WATCH": 2, "NEEDS_REVIEW": 2, "ON_TRACK": 7},
        "jobs_needing_action": 3,
        "total_dollars_at_risk": 66300.0,
        "summary_source": "template",
    }
    assert index["runs"][1]["jobs_needing_action"] == 2
    assert index["runs"][1]["total_dollars_at_risk"] == 58800.0
    assert index["runs"][1]["counts"]["WATCH"] == 4

    assert (
        run_sample(tmp_path, SAMPLE_3_NOV, generated_at="2026-11-03T07:00:00+11:00").exit_code == 0
    )
    rerun = load_json(tmp_path / "runs" / "index.json")
    assert [r["as_of"] for r in rerun["runs"]] == ["2026-11-04", "2026-11-03"]
    assert rerun["runs"][1]["generated_at"] == "2026-11-03T07:00:00+11:00"


def test_ac50_ai_off_uses_template_summary(tmp_path):
    """AC-50: --ai off -> template text, source template, provider none, reason ai_off."""
    summary = _run_4_nov(tmp_path)["summary"]

    assert summary == {
        "text": snapshot("template-summary-2026-11-04.txt").rstrip("\n"),
        "source": "template",
        "provider": "none",
        "model": None,
        "fallback_reason": "ai_off",
        "rejected_tokens": [],
    }


def test_ac51_all_needs_review_is_not_an_error(tmp_path):
    """AC-51: a file whose two jobs are both NEEDS_REVIEW exits 0 with null average margin."""
    base = {
        "name": "Job", "client": "Client", "site": "Site", "stage": "In progress",
        "project_manager": "PM", "quoted_sell_ex_gst": "1000.00",
    }  # fmt: skip
    jobs = [
        {**base, "id": "R1", "percent_complete": None,
         "cost_centres": [{"name": "Labour", "estimated_cost": "500", "actual_cost_to_date": "1"}]},
        {**base, "id": "R2", "percent_complete": 50, "cost_centres": []},
    ]  # fmt: skip
    source = tmp_path / "review-only.json"
    source.write_text(json.dumps({"snapshot_date": "2026-11-04", "jobs": jobs}))
    out = tmp_path / "out"

    result = run_sample(out, source)

    assert result.exit_code == 0, result.output
    doc = load_json(out / "runs" / "2026-11-04.json")
    assert doc["counts"]["NEEDS_REVIEW"] == 2
    assert doc["portfolio"]["average_forecast_margin_pct"] is None
    assert doc["portfolio"]["total_dollars_at_risk"] == 0.0
