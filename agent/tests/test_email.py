"""Graph sendMail payload, subject, email body snapshot and DryRunMailer (AC-41..AC-44)."""

import json
import socket
from datetime import date

import pytest
from cli_helpers import GENERATED_AT_DT, load_json, run_sample, snapshot
from conftest import AS_OF, DEFAULT_THRESHOLDS, SAMPLE_3_NOV, SAMPLE_4_NOV, cc, make_job

from margin_watch.config import load_settings
from margin_watch.email_graph import build_sendmail_payload, build_subject
from margin_watch.mailer import DryRunMailer, EmailDraft
from margin_watch.models import Snapshot
from margin_watch.run import build_report
from margin_watch.sources import SampleFileSource


def _report(jobs=None, path=SAMPLE_4_NOV, as_of=AS_OF):
    snap = (
        SampleFileSource(path).load() if jobs is None else Snapshot(snapshot_date=None, jobs=jobs)
    )
    return build_report(
        snap,
        source_name=path.name,
        as_of=as_of,
        generated_at=GENERATED_AT_DT,
        thresholds=DEFAULT_THRESHOLDS,
    )


def test_ac41_graph_payload_shape(tmp_path):
    """AC-41: exactly the POST /me/sendMail body, recipient from config/settings.toml."""
    assert run_sample(tmp_path).exit_code == 0
    payload = load_json(tmp_path / "email" / "graph-sendmail-2026-11-04.json")

    assert set(payload) == {"message", "saveToSentItems"}
    assert payload["saveToSentItems"] is True
    message = payload["message"]
    assert set(message) == {"subject", "body", "toRecipients"}
    assert set(message["body"]) == {"contentType", "content"}
    assert message["body"]["contentType"] == "HTML"
    assert message["toRecipients"] == [{"emailAddress": {"address": "ops@example.com"}}]
    assert load_settings().email_to == "ops@example.com"


def test_ac41_payload_uses_given_recipient():
    """AC-41: the recipient passed in is the only recipient."""
    payload = build_sendmail_payload(_report(), "someone@example.com")

    assert payload["message"]["toRecipients"] == [
        {"emailAddress": {"address": "someone@example.com"}}
    ]
    assert payload["message"]["subject"] == build_subject(_report())


@pytest.mark.parametrize(
    ("path", "as_of", "expected"),
    [
        (
            SAMPLE_4_NOV,
            date(2026, 11, 4),
            "Margin watch, Wed 4 Nov: 1 loss, 2 at risk, 2 to review",
        ),
        (
            SAMPLE_3_NOV,
            date(2026, 11, 3),
            "Margin watch, Tue 3 Nov: 1 loss, 1 at risk, 2 to review",
        ),
    ],
)
def test_ac42_subject_for_sample_runs(path, as_of, expected):
    """AC-42: subject lines for the two sample runs."""
    assert build_subject(_report(path=path, as_of=as_of)) == expected


def test_ac42_subject_plural_losses():
    """AC-42: two losses read '2 losses'."""
    jobs = (
        make_job([cc("Labour", "90000", "100001")], job_id="L1"),
        make_job([cc("Labour", "90000", "100001")], job_id="L2"),
    )

    assert build_subject(_report(jobs)) == "Margin watch, Wed 4 Nov: 2 losses"


def test_ac42_subject_watch_only():
    """AC-42: only WATCH and ON_TRACK jobs -> '1 on watch'."""
    jobs = (
        make_job([cc("Labour", "70000", "74000")], job_id="W1"),
        make_job([cc("Labour", "80000", "80000")], job_id="K1"),
    )

    assert build_subject(_report(jobs)) == "Margin watch, Wed 4 Nov: 1 on watch"


def test_ac42_subject_all_on_track():
    """AC-42: every job ON_TRACK -> 'all 2 jobs on track'."""
    jobs = (
        make_job([cc("Labour", "80000", "80000")], job_id="K1"),
        make_job([cc("Labour", "80000", "80000")], job_id="K2"),
    )

    assert build_subject(_report(jobs)) == "Margin watch, Wed 4 Nov: all 2 jobs on track"


def test_ac43_email_body_matches_snapshot(tmp_path):
    """AC-43: the HTML body equals the reviewed snapshot; preview file is the same HTML."""
    assert run_sample(tmp_path).exit_code == 0
    content = load_json(tmp_path / "email" / "graph-sendmail-2026-11-04.json")["message"]["body"][
        "content"
    ]
    preview = (tmp_path / "email" / "preview-2026-11-04.html").read_text(encoding="utf-8")
    expected = snapshot("email-2026-11-04.html")

    assert content == expected
    assert preview == expected


def test_ac43_email_lists_only_jobs_that_are_not_on_track(tmp_path):
    """AC-43: the 7 flagged / review jobs appear; no ON_TRACK job id appears."""
    assert run_sample(tmp_path).exit_code == 0
    content = load_json(tmp_path / "email" / "graph-sendmail-2026-11-04.json")["message"]["body"][
        "content"
    ]

    for job_id in ("1042", "1038", "1035", "1033", "1040", "1039", "1044"):
        assert job_id in content
    for job_id in ("1037", "1031", "1032", "1034", "1036", "1041", "1043"):
        assert job_id not in content
    assert content.count("<tr>") == 5 + 1 + 7  # 5 layout rows + table header + 7 job rows
    assert "Template summary" in content
    assert "6:30 AM" in content
    assert "Sample data only" in content
    assert "Dry run" in content


def test_ac44_dry_run_mailer_writes_files_and_opens_no_socket(tmp_path, monkeypatch):
    """AC-44: DryRunMailer writes payload JSON and preview HTML, sends nothing, no socket."""

    def no_sockets(*_args, **_kwargs):
        raise RuntimeError("DryRunMailer must not create a socket")

    monkeypatch.setattr(socket, "socket", no_sockets)
    payload = {"message": {"subject": "Test"}, "saveToSentItems": True}
    draft = EmailDraft(as_of=AS_OF, payload=payload, html="<p>Hello</p>")

    receipt = DryRunMailer(tmp_path / "email").send(draft)

    assert receipt.sent is False
    assert receipt.payload_path == tmp_path / "email" / "graph-sendmail-2026-11-04.json"
    assert receipt.preview_path == tmp_path / "email" / "preview-2026-11-04.html"
    assert json.loads(receipt.payload_path.read_text()) == payload
    assert receipt.payload_path.read_text().startswith('{\n  "message"')
    assert receipt.preview_path.read_text() == "<p>Hello</p>"
