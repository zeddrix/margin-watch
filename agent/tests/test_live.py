"""The live dry run behind the dashboard's Run button (AC-92..AC-95)."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from cli_helpers import load_json

from margin_watch.live import run_live, sample_dates

NOW = datetime(2026, 11, 4, 9, 15, tzinfo=ZoneInfo("Australia/Melbourne"))
STEP_IDS = ["read", "maths", "review", "summary", "excel", "email", "dashboard"]


def _run(tmp_path, ai="demo", **kwargs):
    return list(run_live(as_of="2026-11-04", ai=ai, output_dir=tmp_path, pace=0, now=NOW, **kwargs))


def _done(events, step):
    return next(e for e in events if e.get("step") == step and e["state"] in ("done", "warning"))


def test_ac92_event_sequence_and_titles(tmp_path):
    """AC-92: start (7 steps), running then done for each step in order, then done (not sent)."""
    events = _run(tmp_path)

    start = events[0]
    assert start["type"] == "start"
    assert start["dry_run"] is True
    assert start["ai"] == "demo"
    assert start["as_of"] == "2026-11-04"
    assert start["steps"] == [
        {"id": "read", "title": "Reading the jobs"},
        {"id": "maths", "title": "Doing the maths"},
        {"id": "review", "title": "Catching bad data"},
        {"id": "summary", "title": "AI writes the summary, and every number is checked"},
        {"id": "excel", "title": "Saving the Excel report"},
        {"id": "email", "title": "Drafting the morning email"},
        {"id": "dashboard", "title": "Updating the dashboard"},
    ]
    steps = [(e["step"], e["state"]) for e in events[1:-1]]
    assert steps == [(s, state) for s in STEP_IDS for state in ("running", "done")]
    assert events[-1]["type"] == "done"
    assert events[-1]["sent"] is False
    assert events[-1]["as_of"] == "2026-11-04"


def test_ac92_plain_english_details(tmp_path):
    """AC-92: exact detail sentences for each step."""
    events = _run(tmp_path)

    details = {step: _done(events, step)["detail"] for step in STEP_IDS if step != "summary"}
    assert details == {
        "read": "Read 14 jobs from jobs-2026-11-04.json (sample data shaped like a Simpro export).",
        "maths": "Worked out the quoted and forecast margin for 12 jobs: "
        "1 heading for a loss, 2 at risk, 2 on watch and 7 on track.",
        "review": "2 jobs have missing or wrong data. "
        "They're flagged for review instead of guessed.",
        "excel": "Saved margin-report-2026-11-04.xlsx with three sheets: "
        "Summary, Jobs and Cost centres.",
        "email": "Drafted the email to ops@example.com: "
        "“Margin watch, Wed 4 Nov: 1 loss, 2 at risk, 2 to review”. "
        "Dry run, so it was saved, not sent.",
        "dashboard": "Saved the run so the dashboard can show it.",
    }


def test_ac92_step_data_and_files_written(tmp_path):
    """AC-92: tally, dollars at risk, review jobs, and the same five files as the CLI."""
    events = _run(tmp_path)

    maths = _done(events, "maths")["data"]
    assert maths["counts"] == {"LOSS": 1, "AT_RISK": 2, "WATCH": 2, "NEEDS_REVIEW": 2,
                               "ON_TRACK": 7}  # fmt: skip
    assert maths["dollars_at_risk"] == "$66,300"
    review = _done(events, "review")["data"]["jobs"]
    assert [j["id"] for j in review] == ["1039", "1044"]
    assert review[1]["problem"] == "Materials actual cost to date is negative (-$1,250)."
    assert _done(events, "excel")["data"]["href"] == "/files/margin-report-2026-11-04.xlsx"
    assert _done(events, "email")["data"]["href"] == "/files/email/preview-2026-11-04.html"
    written = (
        "runs/2026-11-04.json",
        "runs/index.json",
        "margin-report-2026-11-04.xlsx",
        "email/graph-sendmail-2026-11-04.json",
        "email/preview-2026-11-04.html",
    )
    for relative in written:
        assert (tmp_path / relative).is_file(), relative
    assert load_json(tmp_path / "runs" / "2026-11-04.json")["generated_at"] == (
        "2026-11-04T09:15:00+11:00"
    )


def test_ac93_demo_numbers_all_verified(tmp_path):
    """AC-93: demo -> verified, every number check ok, detail counts the numbers."""
    summary = _done(_run(tmp_path), "summary")

    data = summary["data"]
    tokens = [c["token"] for c in data["checks"]]
    assert summary["state"] == "done"
    assert data["verified"] is True
    assert data["writer"] == "Demo AI"
    assert data["rejected"] == []
    assert all(c["ok"] for c in data["checks"])
    for token in ("-2.5%", "17.5%", "$12,000", "$66,300"):
        assert token in tokens
    assert summary["detail"] == (
        f"Demo AI wrote the summary. All {len(tokens)} numbers in it match the calculations, "
        "so it was approved."
    )


def test_ac93_made_up_number_is_caught_live(tmp_path):
    """AC-93: demo-bad -> warning, $13,750 not ok, everything else ok, template saved."""
    summary = _done(_run(tmp_path, ai="demo-bad"), "summary")

    data = summary["data"]
    bad = [c for c in data["checks"] if not c["ok"]]
    assert summary["state"] == "warning"
    assert data["verified"] is False
    assert data["rejected"] == ["$13,750"]
    assert bad == [{"token": "$13,750", "ok": False}]
    assert len(data["checks"]) > 5
    assert summary["detail"] == (
        "Demo AI wrote a summary, but $13,750 isn't in the calculations. "
        "The answer was rejected and the safe template summary was used instead."
    )
    saved = load_json(tmp_path / "runs" / "2026-11-04.json")["summary"]
    assert saved["source"] == "template"
    assert saved["rejected_tokens"] == ["$13,750"]


def test_ac94_paced_for_people(tmp_path):
    """AC-94: pace 0.9 -> one 0.9 s wait after each of the 7 steps; pace 0 -> no waits."""
    waits: list[float] = []

    list(run_live(as_of="2026-11-04", ai="demo", output_dir=tmp_path / "a", pace=0.9,
                  sleep=waits.append, now=NOW))  # fmt: skip
    assert waits == [0.9] * 7

    none: list[float] = []
    list(run_live(as_of="2026-11-04", ai="demo", output_dir=tmp_path / "b", pace=0,
                  sleep=none.append, now=NOW))  # fmt: skip
    assert none == []


def test_ac95_invalid_file_is_an_error_event(tmp_path):
    """AC-95: an invalid sample file -> error event for 'read', no done event."""
    broken = tmp_path / "broken.json"
    broken.write_text("{ not json")

    events = list(run_live(as_of="2026-11-04", ai="demo", output_dir=tmp_path / "out",
                           source=broken, pace=0, now=NOW))  # fmt: skip

    error = events[-1]
    assert error["type"] == "error"
    assert error["step"] == "read"
    assert error["message"].startswith("Invalid input file:")
    assert all(e["type"] != "done" for e in events)
    assert json.dumps(events)  # every event is plain JSON for the stream


def test_ac96_sample_dates():
    """AC-96: the helper offers the two sample dates, oldest first."""
    assert sample_dates() == ["2026-11-03", "2026-11-04"]
