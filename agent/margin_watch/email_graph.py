"""The morning email as a Microsoft Graph `POST /me/sendMail` request body.

Simple table layout with inline styles so it renders in Outlook. Only jobs that aren't
ON_TRACK are listed. See docs/acceptance-criteria.md, AC-41..AC-43.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any
from zoneinfo import ZoneInfo

from margin_watch.formatting import format_date, format_money, format_pct
from margin_watch.labels import STATUS_WORDS, summary_label
from margin_watch.models import JobAssessment, RunReport, Status

MELBOURNE = ZoneInfo("Australia/Melbourne")

_PILL_COLOURS: dict[Status, tuple[str, str]] = {
    Status.LOSS: ("#fee2e2", "#991b1b"),
    Status.AT_RISK: ("#ffedd5", "#9a3412"),
    Status.WATCH: ("#fef9c3", "#854d0e"),
    Status.NEEDS_REVIEW: ("#e2e8f0", "#334155"),
    Status.ON_TRACK: ("#dcfce7", "#166534"),
}
_TH = "padding:8px;border-bottom:2px solid #cbd5e1;font-size:12px;color:#475569;"
_TD = "padding:8px;border-bottom:1px solid #e2e8f0;vertical-align:top;"
_MUTED = "color:#475569;"


def _text(value: str) -> str:
    return escape(value, quote=False)


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def build_subject(report: RunReport) -> str:
    counts = report.portfolio.counts
    day = format_date(report.as_of).rsplit(" ", 1)[0]  # "Wed 4 Nov"
    parts = []
    if counts[Status.LOSS]:
        parts.append(_plural(counts[Status.LOSS], "loss", "losses"))
    if counts[Status.AT_RISK]:
        parts.append(f"{counts[Status.AT_RISK]} at risk")
    if counts[Status.NEEDS_REVIEW]:
        parts.append(f"{counts[Status.NEEDS_REVIEW]} to review")
    if not parts and counts[Status.WATCH]:
        parts.append(f"{counts[Status.WATCH]} on watch")
    if not parts:
        parts.append(f"all {_plural(report.portfolio.total_jobs, 'job', 'jobs')} on track")
    return f"Margin watch, {day}: {', '.join(parts)}"


def _clock(moment: datetime) -> str:
    local = moment.astimezone(MELBOURNE)
    hour = local.hour % 12 or 12
    return f"{hour}:{local.minute:02d} {'AM' if local.hour < 12 else 'PM'}"


def _job_row(assessment: JobAssessment) -> list[str]:
    job = assessment.job
    metrics = assessment.metrics
    background, colour = _PILL_COLOURS[assessment.status]
    pill = (
        "display:inline-block;padding:2px 8px;border-radius:10px;"
        f"background-color:{background};color:{colour};font-weight:bold;white-space:nowrap;"
    )
    forecast = format_pct(metrics.forecast_margin_pct) if metrics else "—"
    at_risk = format_money(metrics.dollars_at_risk) if metrics else "—"
    return [
        "<tr>",
        f'<td style="{_TD}"><span style="{pill}">{STATUS_WORDS[assessment.status]}</span></td>',
        f'<td style="{_TD}">{_text(f"{job.id} {job.name}")}<br>'
        f'<span style="{_MUTED}">{_text(job.client)}</span></td>',
        f'<td style="{_TD}">{_text(job.project_manager)}</td>',
        f'<td align="right" style="{_TD}">{forecast}</td>',
        f'<td align="right" style="{_TD}">{at_risk}</td>',
        f'<td style="{_TD}">{_text(assessment.reason)}</td>',
        "</tr>",
    ]


def build_email_html(report: RunReport) -> str:
    subject = build_subject(report)
    stamp = report.as_of.isoformat()
    paragraphs = [
        f'<p style="margin:0 0 12px 0;">{_text(p)}</p>' for p in report.summary.text.split("\n\n")
    ]
    headers = [("left", "Status"), ("left", "Job"), ("left", "PM"), ("right", "Forecast margin"),
               ("right", "$ at risk"), ("left", "Why")]  # fmt: skip
    rows: list[str] = []
    for assessment in report.assessments:
        if assessment.status != Status.ON_TRACK:
            rows.extend(_job_row(assessment))
    generated = report.generated_at.astimezone(MELBOURNE)
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en-AU">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_text(subject)}</title>",
        "</head>",
        '<body style="margin:0;padding:0;background-color:#f1f5f9;">',
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="background-color:#f1f5f9;">',
        "<tr>",
        '<td align="center" style="padding:24px 12px;">',
        '<table role="presentation" width="680" cellpadding="0" cellspacing="0" border="0" '
        'style="width:680px;max-width:680px;background-color:#ffffff;border:1px solid #e2e8f0;'
        "font-family:'Segoe UI',Arial,sans-serif;color:#0f172a;\">",
        "<tr>",
        '<td style="padding:24px 24px 8px 24px;">',
        '<p style="margin:0 0 4px 0;font-size:12px;color:#475569;">'
        "Sample data · fictional jobs</p>",
        '<h1 style="margin:0;font-size:20px;line-height:28px;color:#0f172a;">'
        f"Margin watch · {format_date(report.as_of)}</h1>",
        "</td>",
        "</tr>",
        "<tr>",
        '<td style="padding:8px 24px 0 24px;font-size:15px;line-height:22px;">',
        *paragraphs,
        '<p style="margin:0 0 16px 0;font-size:12px;line-height:18px;color:#475569;">'
        f"{_text(summary_label(report.summary))}</p>",
        "</td>",
        "</tr>",
        "<tr>",
        '<td style="padding:0 24px 16px 24px;">',
        '<table cellpadding="0" cellspacing="0" border="0" width="100%" '
        'style="border-collapse:collapse;font-size:13px;line-height:18px;">',
        "<tr>",
        *[f'<th align="{align}" style="{_TH}">{_text(name)}</th>' for align, name in headers],
        "</tr>",
        *rows,
        "</table>",
        "</td>",
        "</tr>",
        "<tr>",
        '<td style="padding:16px 24px 24px 24px;border-top:1px solid #e2e8f0;font-size:12px;'
        'line-height:18px;color:#475569;">',
        f'<p style="margin:0 0 8px 0;">Generated by margin-watch at {_clock(generated)} on '
        f"{format_date(generated.date())} (Melbourne time) from {_text(report.source_name)}. "
        f"Full report: margin-report-{stamp}.xlsx.</p>",
        '<p style="margin:0;">Sample data only: these jobs, clients and people are fictional. '
        "Dry run: this email was saved, not sent.</p>",
        "</td>",
        "</tr>",
        "</table>",
        "</td>",
        "</tr>",
        "</table>",
        "</body>",
        "</html>",
    ]
    return "\n".join(lines) + "\n"


def build_sendmail_payload(report: RunReport, recipient: str) -> dict[str, Any]:
    """Exactly the `POST /me/sendMail` request body (Microsoft Graph v1.0)."""
    return {
        "message": {
            "subject": build_subject(report),
            "body": {"contentType": "HTML", "content": build_email_html(report)},
            "toRecipients": [{"emailAddress": {"address": recipient}}],
        },
        "saveToSentItems": True,
    }
