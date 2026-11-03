"""Forecasting and margin maths (docs/acceptance-criteria.md, Phase 2)."""

from decimal import Decimal

from conftest import DEFAULT_THRESHOLDS, cc, make_job
from hypothesis import given, settings
from hypothesis import strategies as st

from margin_watch.calc import compute_metrics, forecast_at_completion, main_driver
from margin_watch.models import Status
from margin_watch.status import assess_job


def _centre(metrics, name):
    return next(c for c in metrics.cost_centres if c.name == name)


def test_ac01_quoted_margin():
    """AC-01: sell $100,000, Labour est $60,000, Materials est $20,000 -> estimated total
    $80,000 and quoted margin exactly 20%."""
    job = make_job(
        [cc("Labour", "60000", "0"), cc("Materials", "20000", "0")], percent_complete="50"
    )

    metrics = compute_metrics(job)

    assert metrics.estimated_total == Decimal("80000")
    assert metrics.quoted_margin_pct == Decimal("20")


def test_ac02_burn_rate_forecast():
    """AC-02: 40% complete, Labour est $10,000, actual $5,000 -> forecast $12,500,
    overrun $2,500 and 25%."""
    job = make_job([cc("Labour", "10000", "5000")], percent_complete="40")

    labour = _centre(compute_metrics(job), "Labour")

    assert labour.forecast_at_completion == Decimal("12500")
    assert labour.overrun_dollars == Decimal("2500")
    assert labour.overrun_pct == Decimal("25")
    assert forecast_at_completion(cc("Labour", "10000", "5000"), Decimal("40")) == Decimal("12500")


def test_ac03_forecast_never_below_estimate_in_progress():
    """AC-03: 50% complete, Labour est $10,000, actual $2,000 -> forecast $10,000,
    overrun $0 and 0%."""
    job = make_job([cc("Labour", "10000", "2000")], percent_complete="50")

    labour = _centre(compute_metrics(job), "Labour")

    assert labour.forecast_at_completion == Decimal("10000")
    assert labour.overrun_dollars == Decimal("0")
    assert labour.overrun_pct == Decimal("0")


def test_ac04_complete_job_uses_actual_below_estimate():
    """AC-04: 100% complete, Labour est $10,000, actual $8,000 -> forecast $8,000,
    overrun -$2,000 (-20%)."""
    job = make_job([cc("Labour", "10000", "8000")], percent_complete="100")

    labour = _centre(compute_metrics(job), "Labour")

    assert labour.forecast_at_completion == Decimal("8000")
    assert labour.overrun_dollars == Decimal("-2000")
    assert labour.overrun_pct == Decimal("-20")


def test_ac04_complete_job_uses_actual_above_estimate():
    """AC-04: 100% complete, Labour est $10,000, actual $12,000 -> forecast $12,000,
    overrun $2,000 (20%)."""
    labour = _centre(
        compute_metrics(make_job([cc("Labour", "10000", "12000")], percent_complete="100")),
        "Labour",
    )

    assert labour.forecast_at_completion == Decimal("12000")
    assert labour.overrun_dollars == Decimal("2000")
    assert labour.overrun_pct == Decimal("20")


def test_ac05_not_started_job_forecasts_the_estimate():
    """AC-05: 0% complete, all actuals $0, Labour est $10,000 -> forecast $10,000,
    not NEEDS_REVIEW."""
    job = make_job([cc("Labour", "10000", "0")], percent_complete="0")

    assessment = assess_job(job, DEFAULT_THRESHOLDS)

    assert assessment.status != Status.NEEDS_REVIEW
    assert assessment.status == Status.ON_TRACK
    assert assessment.metrics is not None
    assert _centre(assessment.metrics, "Labour").forecast_at_completion == Decimal("10000")


def test_ac06_job_forecast_margin_erosion_and_dollars_at_risk():
    """AC-06: sell $100,000, 50% complete, Labour $50,000/$30,000, Materials $30,000/$15,000 ->
    forecast total $90,000, forecast 10%, quoted 20%, erosion 10 pts, $10,000 at risk."""
    job = make_job(
        [cc("Labour", "50000", "30000"), cc("Materials", "30000", "15000")],
        percent_complete="50",
    )

    metrics = compute_metrics(job)

    assert metrics.forecast_total == Decimal("90000")
    assert metrics.forecast_margin_pct == Decimal("10")
    assert metrics.quoted_margin_pct == Decimal("20")
    assert metrics.margin_erosion_pts == Decimal("10")
    assert metrics.dollars_at_risk == Decimal("10000")
    assert _centre(metrics, "Labour").forecast_at_completion == Decimal("60000")
    assert _centre(metrics, "Materials").forecast_at_completion == Decimal("30000")


def test_ac07_dollars_at_risk_never_negative():
    """AC-07: 100% complete, est $80,000, actual $70,000 -> $0 at risk, forecast 30%,
    erosion -10 pts."""
    metrics = compute_metrics(make_job([cc("Labour", "80000", "70000")]))

    assert metrics.dollars_at_risk == Decimal("0")
    assert metrics.forecast_margin_pct == Decimal("30")
    assert metrics.margin_erosion_pts == Decimal("-10")


def test_ac08_overrun_pct_is_null_for_zero_estimate():
    """AC-08: Equipment hire est $0, actual $500, 100% complete -> overrun $500, overrun % null."""
    job = make_job([cc("Labour", "50000", "50000"), cc("Equipment hire", "0", "500")])

    hire = _centre(compute_metrics(job), "Equipment hire")

    assert hire.overrun_dollars == Decimal("500")
    assert hire.overrun_pct is None
    assert hire.forecast_at_completion == Decimal("500")


def test_ac23_main_driver_function_ignores_status():
    """AC-23: main_driver() on metrics picks the largest dollar overrun, or None if nothing
    is over its estimate."""
    over = compute_metrics(
        make_job([cc("Labour", "70000", "71000"), cc("Materials", "1000", "900")])
    )
    under = compute_metrics(make_job([cc("Labour", "70000", "70000")]))

    assert main_driver(over) == "Labour"
    assert main_driver(under) is None


_money = st.decimals(min_value=Decimal("0"), max_value=Decimal("1000000"), places=2)


@st.composite
def _overrunning_job(draw):
    percent = draw(st.integers(min_value=1, max_value=100))
    centres = []
    for index in range(draw(st.integers(min_value=1, max_value=4))):
        estimate = draw(_money)
        forecast = estimate + draw(_money)
        actual = forecast * Decimal(percent) / Decimal(100)
        centres.append(cc(f"Centre {index}", str(estimate), str(actual)))
    sell = draw(st.decimals(min_value=Decimal("0.01"), max_value=Decimal("10000000"), places=2))
    return make_job(centres, sell=str(sell), percent_complete=str(percent))


@settings(max_examples=300, deadline=None)
@given(_overrunning_job())
def test_ac32_property_overruns_never_improve_margin(job):
    """AC-32: if every cost centre's forecast >= its estimate, forecast margin <= quoted margin
    and dollars at risk equals the sum of overrun dollars."""
    metrics = compute_metrics(job)

    assert all(c.forecast_at_completion >= c.estimated_cost for c in metrics.cost_centres)
    assert metrics.forecast_margin_pct <= metrics.quoted_margin_pct
    assert metrics.dollars_at_risk == sum(
        (c.overrun_dollars for c in metrics.cost_centres), Decimal(0)
    )
