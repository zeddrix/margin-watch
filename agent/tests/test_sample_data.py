"""Both sample snapshots against the hand-calculated tables in docs/spec.md (AC-29..AC-31)."""

from decimal import Decimal

from conftest import DEFAULT_THRESHOLDS, SAMPLE_3_NOV, SAMPLE_4_NOV, cc, make_job

from margin_watch.calc import summarise_portfolio
from margin_watch.models import Status
from margin_watch.sources import SampleFileSource
from margin_watch.status import assess_jobs

L, A, W, R, OK = (Status.LOSS, Status.AT_RISK, Status.WATCH, Status.NEEDS_REVIEW, Status.ON_TRACK)
ON_TRACK_20 = "Forecast margin 20.0% against 20.0% quoted, within thresholds."

# (id, status, quoted %, forecast %, erosion pts, $ at risk, main driver, reason); None = no metrics
EXPECTED_4_NOV = [
    (
        "1042",
        L,
        "17.5",
        "-2.5",
        "20",
        "16000",
        "Labour",
        "Heading for a loss: forecast margin -2.5% against 17.5% quoted. "
        "Main driver: Labour, projected $12,000 (50.0%) over estimate.",
    ),
    (
        "1038",
        A,
        "20",
        "10.8",
        "9.2",
        "23000",
        "Labour",
        "Margin has eroded 9.2 pts since quote, past the 8.0 pts limit. "
        "Main driver: Labour, projected $18,000 (25.0%) over estimate.",
    ),
    (
        "1035",
        A,
        "20",
        "8.8",
        "11.2",
        "14000",
        "Labour",
        "Forecast margin 8.8% is below the 10.0% floor (quoted 20.0%). "
        "Main driver: Labour, projected $10,000 (25.0%) over estimate.",
    ),
    (
        "1033",
        W,
        "25",
        "20",
        "5",
        "8000",
        "Labour",
        "Margin has eroded 5.0 pts since quote. "
        "Main driver: Labour, projected $5,600 (14.0%) over estimate.",
    ),
    (
        "1040",
        W,
        "25",
        "24.5",
        "0.5",
        "300",
        "Equipment hire",
        "Equipment hire is projected $300 (15.0%) over estimate.",
    ),
    (
        "1039",
        R,
        None,
        None,
        None,
        None,
        None,
        "Percent complete is missing, so the forecast can't be worked out.",
    ),
    (
        "1044",
        R,
        None,
        None,
        None,
        None,
        None,
        "Materials actual cost to date is negative (-$1,250).",
    ),
    (
        "1037",
        OK,
        "20",
        "17.5",
        "2.5",
        "5000",
        None,
        "Forecast margin 17.5% against 20.0% quoted, within thresholds.",
    ),
    (
        "1031",
        OK,
        "20",
        "22",
        "-2",
        "0",
        None,
        "Forecast margin 22.0% against 20.0% quoted, within thresholds.",
    ),
    ("1032", OK, "20", "20", "0", "0", None, ON_TRACK_20),
    ("1034", OK, "20", "20", "0", "0", None, ON_TRACK_20),
    ("1036", OK, "20", "20", "0", "0", None, ON_TRACK_20),
    (
        "1041",
        OK,
        "25",
        "25",
        "0",
        "0",
        None,
        "Forecast margin 25.0% against 25.0% quoted, within thresholds.",
    ),
    ("1043", OK, "20", "20", "0", "0", None, ON_TRACK_20),
]

EXPECTED_3_NOV = [
    (
        "1042",
        L,
        "17.5",
        "-1.25",
        "18.75",
        "15000",
        "Labour",
        "Heading for a loss: forecast margin -1.3% against 17.5% quoted. "
        "Main driver: Labour, projected $11,000 (45.8%) over estimate.",
    ),
    EXPECTED_4_NOV[2],  # 1035, unchanged
    (
        "1038",
        W,
        "20",
        "15.2",
        "4.8",
        "12000",
        "Labour",
        "Margin has eroded 4.8 pts since quote. "
        "Main driver: Labour, projected $12,000 (16.7%) over estimate.",
    ),
    EXPECTED_4_NOV[3],  # 1033, unchanged
    (
        "1036",
        W,
        "20",
        "15",
        "5",
        "4500",
        "Materials",
        "Margin has eroded 5.0 pts since quote. "
        "Main driver: Materials, projected $4,500 (10.0%) over estimate.",
    ),
    EXPECTED_4_NOV[4],  # 1040, unchanged (exactly 15% overrun)
    EXPECTED_4_NOV[5],
    EXPECTED_4_NOV[6],
    EXPECTED_4_NOV[7],
    EXPECTED_4_NOV[8],
    EXPECTED_4_NOV[9],
    EXPECTED_4_NOV[10],
    EXPECTED_4_NOV[12],
    EXPECTED_4_NOV[13],
]


def _assess(path):
    return assess_jobs(SampleFileSource(path).load().jobs, DEFAULT_THRESHOLDS)


def _row(assessment):
    m = assessment.metrics
    figures = (
        (None, None, None, None)
        if m is None
        else (
            m.quoted_margin_pct,
            m.forecast_margin_pct,
            m.margin_erosion_pts,
            m.dollars_at_risk,
        )
    )
    return (
        assessment.job.id,
        assessment.status,
        *figures,
        assessment.main_driver,
        assessment.reason,
    )


def _expected_row(row):
    job_id, status, q, f, e, risk, driver, reason = row
    return (job_id, status, _dec(q), _dec(f), _dec(e), _dec(risk), driver, reason)


def _dec(value):
    return None if value is None else Decimal(value)


def test_ac29_sample_4_nov_matches_spec_table():
    """AC-29: 4 Nov order, statuses, figures, main drivers and reasons match docs/spec.md."""
    actual = [_row(a) for a in _assess(SAMPLE_4_NOV)]

    assert actual == [_expected_row(r) for r in EXPECTED_4_NOV]


def test_ac29_sample_4_nov_review_codes_and_threshold_job():
    """AC-29: 1039 and 1044 carry their review codes; 1040 sits exactly on the 15% overrun line."""
    by_id = {a.job.id: a for a in _assess(SAMPLE_4_NOV)}
    hire = next(c for c in by_id["1040"].metrics.cost_centres if c.name == "Equipment hire")

    assert by_id["1039"].review_code == "missing_percent_complete"
    assert by_id["1044"].review_code == "negative_cost"
    assert hire.overrun_pct == Decimal("15")
    assert hire.forecast_at_completion == Decimal("2300")


def test_ac30_sample_3_nov_matches_spec_table():
    """AC-30: 3 Nov order, statuses, figures, main drivers and reasons match docs/spec.md."""
    actual = [_row(a) for a in _assess(SAMPLE_3_NOV)]

    assert actual == [_expected_row(r) for r in EXPECTED_3_NOV]


def test_ac31_portfolio_4_nov():
    """AC-31: 4 Nov counts 1/2/2/2/7, needing action 3, to review 2, $66,300, average 15.7394%."""
    summary = summarise_portfolio(_assess(SAMPLE_4_NOV))

    assert summary.counts == {L: 1, A: 2, W: 2, R: 2, OK: 7}
    assert summary.total_jobs == 14
    assert summary.jobs_needing_action == 3
    assert summary.jobs_to_review == 2
    assert summary.total_dollars_at_risk == Decimal("66300")
    assert summary.average_forecast_margin_pct is not None
    assert summary.average_forecast_margin_pct.quantize(Decimal("0.0001")) == Decimal("15.7394")


def test_ac31_portfolio_3_nov():
    """AC-31: 3 Nov counts 1/1/4/2/6, needing action 2, $58,800, average 16.3389%."""
    summary = summarise_portfolio(_assess(SAMPLE_3_NOV))

    assert summary.counts == {L: 1, A: 1, W: 4, R: 2, OK: 6}
    assert summary.jobs_needing_action == 2
    assert summary.jobs_to_review == 2
    assert summary.total_dollars_at_risk == Decimal("58800")
    assert summary.average_forecast_margin_pct is not None
    assert summary.average_forecast_margin_pct.quantize(Decimal("0.0001")) == Decimal("16.3389")


def test_ac31_portfolio_all_needs_review():
    """AC-31: when every job is NEEDS_REVIEW, total at risk is $0 and there is no average."""
    jobs = [make_job([cc()], job_id="X1", percent_complete=None), make_job([], job_id="X2")]

    summary = summarise_portfolio(assess_jobs(jobs, DEFAULT_THRESHOLDS))

    assert summary.counts == {L: 0, A: 0, W: 0, R: 2, OK: 0}
    assert summary.jobs_needing_action == 0
    assert summary.total_dollars_at_risk == Decimal("0")
    assert summary.average_forecast_margin_pct is None
