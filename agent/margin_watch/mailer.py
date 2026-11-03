"""Mailers. `DryRunMailer` writes the Graph payload and an HTML preview and sends nothing.

`GraphMailer` (documented only, see docs/spec.md) would POST the same payload to
https://graph.microsoft.com/v1.0/me/sendMail with a delegated `Mail.Send` token.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class EmailDraft:
    as_of: date
    payload: dict[str, Any]
    html: str


@dataclass(frozen=True)
class MailReceipt:
    sent: bool
    payload_path: Path
    preview_path: Path


class Mailer(Protocol):
    def send(self, draft: EmailDraft) -> MailReceipt: ...


class DryRunMailer:
    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir

    def send(self, draft: EmailDraft) -> MailReceipt:
        raise NotImplementedError
