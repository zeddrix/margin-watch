"""Template summary wording (AC-45)."""

from cli_helpers import snapshot
from conftest import DEFAULT_THRESHOLDS, SAMPLE_4_NOV, cc, make_job

from margin_watch.calc import summarise_portfolio
from margin_watch.sources import SampleFileSource
from margin_watch.status import assess_jobs
from margin_watch.template import template_summary


def _summary(jobs):
    assessments = assess_jobs(jobs, DEFAULT_THRESHOLDS)
    return template_summary(assessments, summarise_portfolio(assessments))


def test_ac45_template_summary_4_nov_matches_snapshot():
    """AC-45: the 4 Nov template text equals the reviewed snapshot."""
    text = _summary(SampleFileSource(SAMPLE_4_NOV).load().jobs)

    assert text + "\n" == snapshot("template-summary-2026-11-04.txt")
    assert "\n\n" in text
    assert not text.endswith("\n")


def test_ac45_template_summary_all_on_track():
    """AC-45: two ON_TRACK jobs with no overrun -> exactly 'Of 2 jobs, 2 are on track.'"""
    jobs = [
        make_job([cc("Labour", "80000", "80000")], job_id="K1"),
        make_job([cc("Labour", "80000", "80000")], job_id="K2"),
    ]

    assert _summary(jobs) == "Of 2 jobs, 2 are on track."


def test_ac45_template_summary_single_review_job():
    """AC-45: one NEEDS_REVIEW job -> singular wording and the data-check line."""
    jobs = [
        make_job([cc()], job_id="X1", name="Pump swap", pm="Ann Lee", percent_complete=None),
    ]

    assert _summary(jobs) == (
        "Of 1 job, 1 needs a data check.\n\nData to check in Simpro: X1 Pump swap (Ann Lee)."
    )
