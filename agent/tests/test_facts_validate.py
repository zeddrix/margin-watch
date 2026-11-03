"""Facts object and the number validator (AC-52..AC-57)."""

import pytest
from summary_helpers import report_4_nov

from margin_watch.facts import build_facts
from margin_watch.validate import allowed_tokens, extract_tokens, validate_text

LOSS_1042 = (
    "Heading for a loss: forecast margin -2.5% against 17.5% quoted. "
    "Main driver: Labour, projected $12,000 (50.0%) over estimate."
)


def _leaves(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _leaves(item)
    elif isinstance(value, list):
        for item in value:
            yield from _leaves(item)
    else:
        yield value


def test_ac52_every_fact_is_a_string():
    """AC-52: every leaf value in the facts object is a pre-formatted string."""
    facts = build_facts(report_4_nov())

    assert set(facts) == {"overview", "jobs"}
    assert all(isinstance(leaf, str) for leaf in _leaves(facts))


def test_ac52_overview_facts_4_nov():
    """AC-52: the 4 Nov overview strings and the flagged jobs in risk order."""
    overview = build_facts(report_4_nov())["overview"]

    assert overview["run_date"] == "Wed 4 Nov 2026"
    assert overview["total_jobs"] == "14"
    assert overview["jobs_needing_action"] == "3"
    assert overview["jobs_to_review"] == "2"
    assert overview["total_dollars_at_risk"] == "$66,300"
    assert overview["average_forecast_margin"] == "15.7%"
    assert overview["counts"] == {"loss": "1", "at_risk": "2", "watch": "2",
                                  "needs_review": "2", "on_track": "7"}  # fmt: skip
    assert [j["job_id"] for j in overview["flagged_jobs"]] == [
        "1042", "1038", "1035", "1033", "1040", "1039", "1044",
    ]  # fmt: skip


def test_ac52_job_facts_1042_and_review_job():
    """AC-52: job 1042's facts exactly; 1039 has its problem and no margin figures."""
    jobs = build_facts(report_4_nov())["jobs"]

    assert set(jobs) == {"1042", "1038", "1035", "1033", "1040", "1039", "1044"}
    assert jobs["1042"] == {
        "job_id": "1042",
        "name": "Chiller replacement, cold-storage warehouse",
        "client": "Frostline Logistics",
        "site": "Frostline cold store, Dandenong South",
        "project_manager": "Dave Kowalski",
        "status": "LOSS",
        "percent_complete": "60.0%",
        "quoted_margin": "17.5%",
        "forecast_margin": "-2.5%",
        "margin_erosion": "20.0 pts",
        "dollars_at_risk": "$16,000",
        "main_driver": "Labour",
        "main_driver_overrun": "$12,000",
        "main_driver_overrun_pct": "50.0%",
        "reason": LOSS_1042,
    }
    review = jobs["1039"]
    assert review["status"] == "NEEDS_REVIEW"
    assert review["review_problem"] == (
        "Percent complete is missing, so the forecast can't be worked out."
    )
    assert review["what_to_check"]
    assert "quoted_margin" not in review
    assert "dollars_at_risk" not in review


def test_ac53_exact_numbers_pass():
    """AC-53: money, %, pts and integers from the facts all pass."""
    allowed = allowed_tokens(build_facts(report_4_nov()))
    text = "Labour is $12,000 (50.0%) over and erosion is 20.0 pts, so 3 jobs need a call."

    result = validate_text(text, allowed)

    assert result.ok is True
    assert result.rejected == ()
    assert extract_tokens(text) == ["$12,000", "50.0%", "20.0pts", "3"]


def test_ac54_invented_money_is_rejected():
    """AC-54: '$15,000' isn't in the 4 Nov facts -> rejected."""
    allowed = allowed_tokens(build_facts(report_4_nov()))

    result = validate_text("It is about $15,000 over.", allowed)

    assert result.ok is False
    assert result.rejected == ("$15,000",)


def test_ac54_invented_integer_listed_once():
    """AC-54: an invented plain integer is rejected and listed once, in order."""
    allowed = allowed_tokens(build_facts(report_4_nov()))

    result = validate_text("Send 12 crews. Yes, 12 crews, and $99 of pies.", allowed)

    assert result.ok is False
    assert result.rejected == ("12", "$99")


@pytest.mark.parametrize("text", ["6%", "$12,500", "8 pts", "2.5%", "$12.5k", "margin of 6 %"])
def test_ac55_re_rounded_numbers_are_rejected(text):
    """AC-55: re-rounded, re-signed or abbreviated forms of real facts are rejected."""
    allowed = allowed_tokens({"a": "6.2%", "b": "$12,480", "c": "8.1 pts", "d": "-2.5%"})

    assert validate_text(text, allowed).ok is False


def test_ac55_exact_forms_pass():
    """AC-55: the exact forms of the same facts pass."""
    allowed = allowed_tokens({"a": "6.2%", "b": "$12,480", "c": "8.1 pts", "d": "-2.5%"})

    result = validate_text("Margin 6.2%, $12,480 over, 8.1 pts eroded, now -2.5%.", allowed)

    assert result.ok is True


def test_ac56_identifiers_and_dates_pass():
    """AC-56: job ids, numbers in names and dates from the facts don't trip the validator."""
    allowed = allowed_tokens(
        {"job_id": "1042", "name": "Level 4 fit-out: VRF install", "run_date": "Wed 4 Nov 2026"}
    )

    result = validate_text("Job 1042 (Level 4 fit-out, Q4 programme) on 4 Nov 2026.", allowed)

    assert result.ok is True
    assert "Q4" not in extract_tokens("Q4 programme")
    assert extract_tokens("Q4 programme") == []


def test_ac57_unit_spelling_and_unicode_minus():
    """AC-57: '20.0 points' matches '20.0 pts' and a Unicode minus matches '-'."""
    allowed = allowed_tokens({"e": "20.0 pts", "f": "-2.5%"})

    unicode_minus = chr(0x2212)
    text = f"Erosion is 20.0 points and margin is {unicode_minus}2.5%."
    assert validate_text(text, allowed).ok is True
    assert validate_text("Erosion is 20 points.", allowed).ok is False
