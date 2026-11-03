"""Words and colours shared by the Excel report, the email and the CLI."""

from __future__ import annotations

from margin_watch.models import Status, Summary

STATUS_WORDS: dict[Status, str] = {
    Status.LOSS: "LOSS",
    Status.AT_RISK: "AT RISK",
    Status.WATCH: "WATCH",
    Status.NEEDS_REVIEW: "NEEDS REVIEW",
    Status.ON_TRACK: "ON TRACK",
}

PROVIDER_NAMES: dict[str, str] = {
    "demo": "Demo AI",
    "demo-bad": "Demo AI",
    "local": "Local model",
    "claude": "Claude",
}


# Shown with every NEEDS_REVIEW job (facts for the model, and mirrored in the dashboard).
WHAT_TO_CHECK: dict[str, str] = {
    "no_cost_centres": "Check the job has its cost centres set up in Simpro.",
    "missing_sell": "Check the quoted sell price on the job in Simpro.",
    "non_positive_sell": "Check the quoted sell price on the job in Simpro.",
    "missing_cost": "Check the cost centre's estimate and actual cost in Simpro.",
    "negative_cost": (
        "Look for a credit or reversal posted to the wrong job or cost centre in Simpro."
    ),
    "missing_percent_complete": (
        "Ask the PM for the job's percent complete and update it in Simpro."
    ),
    "percent_out_of_range": "Correct the job's percent complete in Simpro.",
    "zero_percent_with_costs": (
        "Check whether work has started and update the percent complete in Simpro."
    ),
}


def summary_label(summary: Summary) -> str:
    """Who wrote the summary and whether its numbers were verified. Never calls the demo Claude."""
    if summary.source == "ai_verified":
        return f"Written by {PROVIDER_NAMES[summary.provider]} · numbers verified"
    if summary.rejected_tokens:
        return "Template summary · AI answer rejected"
    return "Template summary"
