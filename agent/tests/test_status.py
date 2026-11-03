"""Status rules, NEEDS_REVIEW reasons, main driver, reason text and sort order (Phase 2 ACs)."""

import pytest
from conftest import DEFAULT_THRESHOLDS, cc, make_job

from margin_watch.models import Status
from margin_watch.status import assess_job, assess_jobs, review_problem, sort_assessments


def _assess(job):
    return assess_job(job, DEFAULT_THRESHOLDS)


# --- thresholds: below / at / above ------------------------------------------------------------


@pytest.mark.parametrize(
    ("actual", "expected"),
    [("100001", Status.LOSS), ("100000", Status.AT_RISK), ("99999", Status.AT_RISK)],
)
def test_ac09_loss_below_zero_margin(actual, expected):
    """AC-09: est $90,000; actual $100,001 (-0.001%) is LOSS; $100,000 (exactly 0%) is AT_RISK."""
    assert _assess(make_job([cc("Labour", "90000", actual)])).status == expected


@pytest.mark.parametrize(
    ("cost", "expected"),
    [("90010", Status.AT_RISK), ("90000", Status.ON_TRACK), ("89990", Status.ON_TRACK)],
)
def test_ac10_at_risk_below_ten_pct_forecast_margin(cost, expected):
    """AC-10: estimate = actual; 9.99% is AT_RISK, exactly 10% and 10.01% are ON_TRACK."""
    assert _assess(make_job([cc("Labour", cost, cost)])).status == expected


@pytest.mark.parametrize(
    ("actual", "expected"),
    [("77990", Status.WATCH), ("78000", Status.AT_RISK), ("78010", Status.AT_RISK)],
)
def test_ac11_at_risk_at_eight_pts_erosion(actual, expected):
    """AC-11: Labour est $70,000 (quoted 30%); 7.99 pts is WATCH, exactly 8 and 8.01 are AT_RISK."""
    assessment = _assess(make_job([cc("Labour", "70000", actual)]))

    assert assessment.status == expected
    assert assessment.metrics is not None
    assert assessment.metrics.forecast_margin_pct > 10


@pytest.mark.parametrize(
    ("actual", "expected"),
    [("72990", Status.ON_TRACK), ("73000", Status.WATCH), ("73010", Status.WATCH)],
)
def test_ac12_watch_at_three_pts_erosion(actual, expected):
    """AC-12: 2.99 pts is ON_TRACK; exactly 3 pts and 3.01 pts are WATCH."""
    assert _assess(make_job([cc("Labour", "70000", actual)])).status == expected


@pytest.mark.parametrize(
    ("hire_actual", "expected"),
    [("2299.80", Status.ON_TRACK), ("2300", Status.WATCH), ("2300.20", Status.WATCH)],
)
def test_ac13_watch_at_fifteen_pct_overrun(hire_actual, expected):
    """AC-13: Equipment hire est $2,000; 14.99% is ON_TRACK, exactly 15% and 15.01% are WATCH."""
    job = make_job([cc("Labour", "50000", "50000"), cc("Equipment hire", "2000", hire_actual)])

    assessment = _assess(job)

    assert assessment.status == expected
    assert assessment.metrics is not None
    assert assessment.metrics.margin_erosion_pts < 3


def test_ac14_loss_beats_at_risk_and_watch():
    """AC-14: a loss with erosion >= 8 pts and an overrun >= 15% is LOSS."""
    job = make_job([cc("Labour", "50000", "80000"), cc("Materials", "30000", "30000")])

    assert _assess(job).status == Status.LOSS


def test_ac14_needs_review_beats_loss():
    """AC-14: the same loss-making job with a negative actual cost is NEEDS_REVIEW."""
    job = make_job([cc("Labour", "50000", "80000"), cc("Materials", "30000", "-1")])

    assert _assess(job).status == Status.NEEDS_REVIEW


# --- NEEDS_REVIEW reasons ----------------------------------------------------------------------


def _review(job):
    assessment = _assess(job)
    assert assessment.status == Status.NEEDS_REVIEW
    return assessment.review_code, assessment.reason


def test_ac15_missing_percent_complete():
    """AC-15: percent complete null -> missing_percent_complete with the exact reason."""
    job = make_job([cc("Labour", "10000", "5000")], percent_complete=None)

    assert _review(job) == (
        "missing_percent_complete",
        "Percent complete is missing, so the forecast can't be worked out.",
    )


def test_ac16_percent_complete_above_100():
    """AC-16: percent complete 112 -> percent_out_of_range."""
    job = make_job([cc("Labour", "10000", "5000")], percent_complete="112")

    assert _review(job) == (
        "percent_out_of_range",
        "Percent complete is 112.0%, outside 0 to 100%.",
    )


def test_ac16_percent_complete_negative():
    """AC-16: percent complete -5 -> percent_out_of_range."""
    job = make_job([cc("Labour", "10000", "5000")], percent_complete="-5")

    assert _review(job) == ("percent_out_of_range", "Percent complete is -5.0%, outside 0 to 100%.")


def test_ac16_percent_complete_boundary_at_100():
    """AC-16: 100.01 is NEEDS_REVIEW; exactly 100 is not."""
    over = make_job([cc("Labour", "10000", "5000")], percent_complete="100.01")
    exact = make_job([cc("Labour", "10000", "5000")], percent_complete="100")

    assert _assess(over).status == Status.NEEDS_REVIEW
    assert _assess(over).review_code == "percent_out_of_range"
    assert _assess(exact).status != Status.NEEDS_REVIEW
    assert review_problem(exact) is None


def test_ac17_zero_percent_with_money_spent():
    """AC-17: 0% complete with Labour actual $1,500 -> zero_percent_with_costs."""
    job = make_job(
        [cc("Labour", "10000", "1500"), cc("Materials", "5000", "0")], percent_complete="0"
    )

    assert _review(job) == (
        "zero_percent_with_costs",
        "Percent complete is 0% but $1,500 has been spent.",
    )


def test_ac18_negative_actual_cost():
    """AC-18: Materials actual -$1,250 -> negative_cost."""
    job = make_job([cc("Labour", "10000", "5000"), cc("Materials", "8000", "-1250")])

    assert _review(job) == ("negative_cost", "Materials actual cost to date is negative (-$1,250).")


def test_ac18_negative_estimated_cost():
    """AC-18: Labour estimate -$100 -> negative_cost."""
    job = make_job([cc("Labour", "-100", "0")])

    assert _review(job) == ("negative_cost", "Labour estimated cost is negative (-$100).")


def test_ac19_missing_actual_cost():
    """AC-19: Labour actual null -> missing_cost."""
    job = make_job([cc("Labour", "10000", None)])

    assert _review(job) == ("missing_cost", "Labour actual cost to date is missing.")


def test_ac19_missing_estimated_cost():
    """AC-19: Labour estimate null -> missing_cost."""
    job = make_job([cc("Labour", None, "100")])

    assert _review(job) == ("missing_cost", "Labour estimated cost is missing.")


def test_ac20_sell_missing():
    """AC-20: sell null -> missing_sell."""
    assert _review(make_job([cc()], sell=None)) == ("missing_sell", "Quoted sell price is missing.")


def test_ac20_sell_zero():
    """AC-20: sell $0 -> non_positive_sell."""
    assert _review(make_job([cc()], sell="0")) == (
        "non_positive_sell",
        "Quoted sell price is $0; it must be above $0.",
    )


def test_ac20_sell_negative():
    """AC-20: sell -$500 -> non_positive_sell."""
    assert _review(make_job([cc()], sell="-500")) == (
        "non_positive_sell",
        "Quoted sell price is -$500; it must be above $0.",
    )


def test_ac21_no_cost_centres():
    """AC-21: no cost centres -> no_cost_centres."""
    assert _review(make_job([])) == ("no_cost_centres", "Job has no cost centres.")


def test_ac22_negative_cost_reported_before_missing_percent():
    """AC-22: a negative actual and a missing percent complete -> negative cost is the reason."""
    job = make_job([cc("Materials", "8000", "-1250")], percent_complete=None)

    assert _review(job)[0] == "negative_cost"


def test_ac22_no_cost_centres_reported_before_zero_sell():
    """AC-22: sell $0 and no cost centres -> no_cost_centres."""
    assert _review(make_job([], sell="0"))[0] == "no_cost_centres"


def test_ac22_needs_review_jobs_have_no_metrics_or_driver():
    """AC-22: NEEDS_REVIEW jobs carry no metrics and no main driver (nothing is guessed)."""
    job = make_job([cc("Labour", "50000", "90000")], percent_complete=None)

    assessment = _assess(job)

    assert assessment.metrics is None
    assert assessment.main_driver is None


# --- main driver --------------------------------------------------------------------------------


def test_ac23_driver_is_largest_dollar_overrun_not_percent():
    """AC-23: Materials +$3,000 (10%) beats Equipment hire +$1,000 (50%)."""
    job = make_job(
        [
            cc("Labour", "30000", "30000"),
            cc("Equipment hire", "2000", "3000"),
            cc("Materials", "30000", "33000"),
        ]
    )

    assessment = _assess(job)

    assert assessment.status == Status.WATCH
    assert assessment.main_driver == "Materials"


def test_ac23_driver_tie_is_alphabetical():
    """AC-23: Labour and Materials both +$2,000 -> Labour, even when Materials is listed first."""
    job = make_job([cc("Materials", "20000", "22000"), cc("Labour", "20000", "22000")])

    assessment = _assess(job)

    assert assessment.status == Status.WATCH
    assert assessment.main_driver == "Labour"


def test_ac23_no_driver_without_an_overrun():
    """AC-23: AT_RISK because of a thin quote (estimate = actual $95,000) -> no main driver."""
    assessment = _assess(make_job([cc("Labour", "95000", "95000")]))

    assert assessment.status == Status.AT_RISK
    assert assessment.main_driver is None


def test_ac23_on_track_job_has_no_driver():
    """AC-23: an ON_TRACK job with a small overrun has no main driver."""
    assessment = _assess(make_job([cc("Labour", "70000", "71000")]))

    assert assessment.status == Status.ON_TRACK
    assert assessment.main_driver is None


# --- reason text --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("centres", "status", "reason"),
    [
        (
            [cc("Labour", "70000", "90000"), cc("Materials", "12000", "12000")],
            Status.LOSS,
            "Heading for a loss: forecast margin -2.0% against 18.0% quoted. "
            "Main driver: Labour, projected $20,000 (28.6%) over estimate.",
        ),
        (
            [cc("Labour", "95000", "95000")],
            Status.AT_RISK,
            "Forecast margin 5.0% is below the 10.0% floor (quoted 5.0%).",
        ),
        (
            [cc("Labour", "70000", "79000")],
            Status.AT_RISK,
            "Margin has eroded 9.0 pts since quote, past the 8.0 pts limit. "
            "Main driver: Labour, projected $9,000 (12.9%) over estimate.",
        ),
        (
            [cc("Labour", "70000", "74000")],
            Status.WATCH,
            "Margin has eroded 4.0 pts since quote. "
            "Main driver: Labour, projected $4,000 (5.7%) over estimate.",
        ),
        (
            [cc("Labour", "50000", "50000"), cc("Equipment hire", "2000", "2400")],
            Status.WATCH,
            "Equipment hire is projected $400 (20.0%) over estimate.",
        ),
        (
            [cc("Labour", "50000", "52000"), cc("Equipment hire", "1000", "1200")],
            Status.WATCH,
            "Equipment hire is projected $200 (20.0%) over estimate. "
            "Main driver: Labour, projected $2,000 (4.0%) over estimate.",
        ),
        (
            [cc("Labour", "80000", "80000")],
            Status.ON_TRACK,
            "Forecast margin 20.0% against 20.0% quoted, within thresholds.",
        ),
    ],
    ids=[
        "loss",
        "at-risk-margin",
        "at-risk-erosion",
        "watch-erosion",
        "watch-overrun-same",
        "watch-overrun-other-driver",
        "on-track",
    ],
)
def test_ac24_reason_text(centres, status, reason):
    """AC-24: exact reason sentence for each trigger."""
    assessment = _assess(make_job(centres))

    assert assessment.status == status
    assert assessment.reason == reason
    assert assessment.review_code is None


# --- sort order ---------------------------------------------------------------------------------


def _mixed_jobs():
    return [
        make_job([cc("Labour", "80000", "80000")], job_id="B"),  # ON_TRACK, $0
        make_job([cc("Labour", "80000", "80000")], job_id="A"),  # ON_TRACK, $0
        make_job([cc("Labour", "70000", "71000")], job_id="Z"),  # ON_TRACK, $1,000
        make_job(
            [cc("Labour", "50000", "50000"), cc("Equipment hire", "2000", "2400")], job_id="W2"
        ),  # WATCH, $400
        make_job([cc("Labour", "70000", "74000")], job_id="W1"),  # WATCH, $4,000
        make_job([cc("Labour", "10000", "5000")], job_id="R", percent_complete=None),
        make_job([cc("Labour", "95000", "95000")], job_id="K2"),  # AT_RISK, $0
        make_job([cc("Labour", "95000", "95000")], job_id="K1"),  # AT_RISK, $0
        make_job([cc("Labour", "90000", "100001")], job_id="L"),  # LOSS
    ]


def test_ac25_sort_order():
    """AC-25: LOSS, AT_RISK, WATCH, NEEDS_REVIEW, ON_TRACK; then $ at risk desc; then job id."""
    expected = ["L", "K1", "K2", "W1", "W2", "R", "Z", "A", "B"]

    assessed = assess_jobs(_mixed_jobs(), DEFAULT_THRESHOLDS)
    resorted = sort_assessments(list(reversed(assessed)))

    assert [a.job.id for a in assessed] == expected
    assert [a.job.id for a in resorted] == expected
