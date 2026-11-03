"""The local demo helper: API, files and safety (AC-96..AC-98). No network: handle() is called
directly; make_server() only binds (it never connects)."""

import json

import pytest
from cli_helpers import run_cli
from typer.testing import CliRunner

from margin_watch.cli import app as cli_app
from margin_watch.server import HOST, LiveApp, make_server


@pytest.fixture
def helper(tmp_path):
    dashboard = tmp_path / "build"
    (dashboard / "_app").mkdir(parents=True)
    (dashboard / "index.html").write_text("<!doctype html><title>Margin Watch</title>")
    (dashboard / "_app" / "app.js").write_text("console.log('ok')")
    (tmp_path / "agent").mkdir()
    (tmp_path / "agent" / ".env").write_text("ANTHROPIC_API_KEY=secret")
    output = tmp_path / "output"
    return LiveApp(dashboard_dir=dashboard, output_dir=output, pace=0)


def _body(response):
    if isinstance(response.body, bytes):
        return response.body
    return b"".join(response.body)


def _events(response):
    return [json.loads(line) for line in _body(response).decode().splitlines() if line]


def test_ac96_health(helper):
    """AC-96: GET /api/health -> live, dry run, the sample dates."""
    response = helper.handle("GET", "/api/health")

    assert response.status == 200
    assert json.loads(_body(response)) == {
        "live": True,
        "dry_run": True,
        "sample_dates": ["2026-11-03", "2026-11-04"],
    }


def test_ac96_run_streams_ndjson_for_latest_date(helper):
    """AC-96: POST /api/run {"ai": "demo"} -> 200 NDJSON events for 2026-11-04."""
    response = helper.handle("POST", "/api/run", b'{"ai": "demo"}')

    events = _events(response)
    assert response.status == 200
    assert response.content_type.startswith("application/x-ndjson")
    assert events[0]["type"] == "start"
    assert events[0]["as_of"] == "2026-11-04"
    assert events[-1] == {"type": "done", "as_of": "2026-11-04", "sent": False,
                          "file": "2026-11-04.json"}  # fmt: skip


def test_ac96_run_another_date_with_demo_bad(helper):
    """AC-96: {"ai": "demo-bad", "as_of": "2026-11-03"} runs 3 Nov."""
    events = _events(
        helper.handle("POST", "/api/run", b'{"ai": "demo-bad", "as_of": "2026-11-03"}')
    )

    assert events[0]["as_of"] == "2026-11-03"
    assert events[0]["ai"] == "demo-bad"
    assert events[-1]["type"] == "done"


@pytest.mark.parametrize(
    "body",
    [
        b'{"ai": "claude"}',
        b'{"ai": "local"}',
        b'{"ai": "off"}',
        b'{"ai": "demo", "as_of": "2026-12-25"}',
        b"not json",
    ],
)
def test_ac96_bad_requests_are_rejected(helper, body):
    """AC-96: paid/networked providers, unknown dates and non-JSON bodies -> 400 with an error."""
    response = helper.handle("POST", "/api/run", body)

    assert response.status == 400
    assert json.loads(_body(response))["error"]


def test_ac96_one_run_at_a_time(helper):
    """AC-96: a second run while one is going -> 409; afterwards runs are allowed again."""
    first = helper.handle("POST", "/api/run", b'{"ai": "demo"}')

    second = helper.handle("POST", "/api/run", b'{"ai": "demo"}')
    assert second.status == 409

    _body(first)  # finish the first run
    assert helper.handle("POST", "/api/run", b'{"ai": "demo"}').status == 200


def test_ac96_reset_clears_only_generated_files(helper):
    """AC-96: POST /api/reset deletes run files, reports and email drafts only; returns 204."""
    _body(helper.handle("POST", "/api/run", b'{"ai": "demo"}'))
    output = helper.output_dir
    keep = output / ".gitkeep"
    keep.write_text("")
    (output / "logs").mkdir()
    (output / "logs" / "run.log").write_text("kept")

    response = helper.handle("POST", "/api/reset")

    assert response.status == 204
    assert not (output / "runs" / "index.json").exists()
    assert not (output / "runs" / "2026-11-04.json").exists()
    assert not (output / "margin-report-2026-11-04.xlsx").exists()
    assert not (output / "email" / "preview-2026-11-04.html").exists()
    assert not (output / "email" / "graph-sendmail-2026-11-04.json").exists()
    assert keep.exists()
    assert (output / "logs" / "run.log").read_text() == "kept"
    assert helper.handle("GET", "/runs/index.json").status == 404


def test_ac97_serves_dashboard_runs_and_files(helper):
    """AC-97: index.html, assets, run files and output files are served."""
    _body(helper.handle("POST", "/api/run", b'{"ai": "demo"}'))

    index = helper.handle("GET", "/")
    asset = helper.handle("GET", "/_app/app.js")
    run_index = helper.handle("GET", "/runs/index.json")
    run = helper.handle("GET", "/runs/2026-11-04.json?x=1")
    excel = helper.handle("GET", "/files/margin-report-2026-11-04.xlsx")
    preview = helper.handle("GET", "/files/email/preview-2026-11-04.html")

    assert index.status == 200
    assert b"Margin Watch" in _body(index)
    assert asset.status == 200
    assert json.loads(_body(run_index))["runs"][0]["as_of"] == "2026-11-04"
    assert json.loads(_body(run))["as_of"] == "2026-11-04"
    assert excel.status == 200
    assert excel.content_type == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert _body(excel)[:2] == b"PK"
    assert preview.status == 200
    assert preview.content_type.startswith("text/html")
    assert b"Margin watch" in _body(preview)


@pytest.mark.parametrize(
    "path",
    [
        "/../agent/.env",
        "/runs/../../agent/.env",
        "/files/../agent/.env",
        "/files/runs/index.json",
        "/files/email/../../agent/.env",
        "/runs/missing.json",
        "/%2e%2e/agent/.env",
        "/nothing-here.js",
    ],
)
def test_ac97_nothing_else_is_served(helper, path):
    """AC-97: path tricks, other files under /files/ and missing files -> 404."""
    _body(helper.handle("POST", "/api/run", b'{"ai": "demo"}'))

    response = helper.handle("GET", path)

    assert response.status == 404
    assert b"secret" not in _body(response)


def test_ac98_listens_on_localhost_only(helper):
    """AC-98: the server binds 127.0.0.1 only."""
    server = make_server(helper, 0)
    try:
        assert HOST == "127.0.0.1"
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()


def test_ac98_serve_help_lists_options():
    """AC-98: `margin-watch serve --help` lists --port 4173, --output-dir, --pace 0.9."""
    result = CliRunner().invoke(cli_app, ["serve", "--help"], env={"COLUMNS": "200"})

    assert result.exit_code == 0
    for text in ("--port", "4173", "--output-dir", "--pace", "0.9"):
        assert text in result.output, text
    assert run_cli("--help").exit_code == 0
