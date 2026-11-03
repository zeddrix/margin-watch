"""The morning email as a Microsoft Graph `POST /me/sendMail` request body."""

from __future__ import annotations

from typing import Any

from margin_watch.models import RunReport


def build_subject(report: RunReport) -> str:
    raise NotImplementedError


def build_email_html(report: RunReport) -> str:
    raise NotImplementedError


def build_sendmail_payload(report: RunReport, recipient: str) -> dict[str, Any]:
    raise NotImplementedError
