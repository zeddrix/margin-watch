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


def summary_label(summary: Summary) -> str:
    """Who wrote the summary and whether its numbers were verified. Never calls the demo Claude."""
    if summary.source == "ai_verified":
        return f"Written by {PROVIDER_NAMES[summary.provider]} · numbers verified"
    if summary.rejected_tokens:
        return "Template summary · AI answer rejected"
    return "Template summary"
