"""Mailers. `DryRunMailer` writes the Graph payload and an HTML preview and sends nothing.

`GraphMailer` (documented only, see docs/spec.md and README) would POST the same payload to
https://graph.microsoft.com/v1.0/me/sendMail with a delegated `Mail.Send` token from an
Entra ID app registration.
"""

from __future__ import annotations

import json
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
    """Saves the draft to disk. Never opens a connection."""

    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir

    def send(self, draft: EmailDraft) -> MailReceipt:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        stamp = draft.as_of.isoformat()
        payload_path = self.out_dir / f"graph-sendmail-{stamp}.json"
        preview_path = self.out_dir / f"preview-{stamp}.html"
        payload_path.write_text(
            json.dumps(draft.payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        preview_path.write_text(draft.html, encoding="utf-8")
        return MailReceipt(sent=False, payload_path=payload_path, preview_path=preview_path)
