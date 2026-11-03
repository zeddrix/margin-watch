"""Provider selection through the CLI, labels and the shared system prompt (AC-65, AC-67..AC-70)."""

import httpx
from cli_helpers import GENERATED_AT, load_json
from conftest import REPO_ROOT, SAMPLE_4_NOV
from openpyxl import load_workbook
from summary_helpers import VALID_ANSWER, ScriptedClient, report_4_nov, text_turn, tool_turn
from typer.testing import CliRunner

import margin_watch.summarise as summarise_module
from margin_watch.cli import app
from margin_watch.labels import summary_label
from margin_watch.models import Summary
from margin_watch.summarise import load_system_prompt, summarise

CLEAN_ENV = {
    "MARGIN_WATCH_AI": None,
    "MARGIN_WATCH_ENV_FILE": "",
    "ANTHROPIC_API_KEY": None,
    "MARGIN_WATCH_MODEL": None,
    "LOCAL_LLM_URL": None,
    "LOCAL_LLM_MODEL": None,
}


def _run(out_dir, *args, env=None):
    result = CliRunner().invoke(
        app,
        ["run", "--source", str(SAMPLE_4_NOV), "--generated-at", GENERATED_AT,
         "--output-dir", str(out_dir), *args],
        env=CLEAN_ENV | (env or {}),
    )  # fmt: skip
    assert result.exit_code == 0, result.output
    return load_json(out_dir / "runs" / "2026-11-04.json")["summary"]


def test_ac68_default_provider_is_demo(tmp_path):
    """AC-68: no --ai and no MARGIN_WATCH_AI -> demo, verified."""
    summary = _run(tmp_path)

    assert summary["source"] == "ai_verified"
    assert summary["provider"] == "demo"
    assert summary["model"] == "demo-scripted-1"


def test_ac68_env_var_selects_provider(tmp_path):
    """AC-68: MARGIN_WATCH_AI=off -> template."""
    summary = _run(tmp_path, env={"MARGIN_WATCH_AI": "off"})

    assert summary["source"] == "template"
    assert summary["fallback_reason"] == "ai_off"


def test_ac68_flag_beats_env_var(tmp_path):
    """AC-68: --ai off beats MARGIN_WATCH_AI=demo."""
    summary = _run(tmp_path, "--ai", "off", env={"MARGIN_WATCH_AI": "demo"})

    assert summary["provider"] == "none"
    assert summary["source"] == "template"


def test_ac65_cli_claude_without_key_exits_zero(tmp_path):
    """AC-65: --ai claude with no key exits 0 and records no_api_key."""
    summary = _run(tmp_path, "--ai", "claude")

    assert summary["source"] == "template"
    assert summary["provider"] == "claude"
    assert summary["model"] == "claude-sonnet-5-5"
    assert summary["fallback_reason"] == "no_api_key"


def test_ac67_cli_local_unreachable_exits_zero(tmp_path, monkeypatch):
    """AC-67: --ai local against an unreachable server exits 0 with the template."""

    def refuse(request):
        raise httpx.ConnectError("connection refused", request=request)

    monkeypatch.setattr(summarise_module, "LOCAL_TRANSPORT", httpx.MockTransport(refuse))

    summary = _run(tmp_path, "--ai", "local", env={"LOCAL_LLM_URL": "http://localhost:9"})

    assert summary["source"] == "template"
    assert summary["provider"] == "local"
    assert summary["fallback_reason"] == "unreachable"


def test_ac69_labels_in_email_and_excel(tmp_path):
    """AC-69: demo -> 'Written by Demo AI · numbers verified'; demo-bad -> 'AI answer rejected'."""
    cases = {"demo": "Written by Demo AI · numbers verified",
             "demo-bad": "Template summary · AI answer rejected"}  # fmt: skip
    for ai, label in cases.items():
        out = tmp_path / ai
        summary = _run(out, "--ai", ai)
        email = (out / "email" / "preview-2026-11-04.html").read_text(encoding="utf-8")
        sheet = load_workbook(out / "margin-report-2026-11-04.xlsx")["Summary"]
        written_by = next(r[1].value for r in sheet.iter_rows() if r[0].value == "Written by")

        assert label in email
        assert written_by == label
        assert "Claude" not in label
        assert summary["provider"] == ai


def test_ac69_labels_for_local_and_claude():
    """AC-69: verified local and Claude labels."""

    def verified(provider):
        return Summary(text="x", source="ai_verified", provider=provider, model="m",
                       fallback_reason=None)  # fmt: skip

    assert summary_label(verified("local")) == "Written by Local model · numbers verified"
    assert summary_label(verified("claude")) == "Written by Claude · numbers verified"
    assert "Claude" not in summary_label(verified("demo"))


def test_ac70_system_prompt_rules():
    """AC-70: the prompt file states the audience, tone, length, number and format rules."""
    text = (REPO_ROOT / "prompts" / "summary_system.md").read_text()
    lowered = text.lower()

    assert load_system_prompt() == text
    for phrase in ("ops manager", "hvac", "australian english", "3 to 6 sentences",
                   "needs action today", "project manager", "exactly",
                   "never calculate, round, add", "estimate", "leave it out",
                   "no greeting", "sign-off"):  # fmt: skip
        assert phrase in lowered, phrase


def test_ac70_every_provider_gets_the_same_system_prompt():
    """AC-70: the summary loop passes exactly the prompt file text as the system prompt."""
    client = ScriptedClient(tool_turn("1042"), text_turn(VALID_ANSWER))

    summarise(report_4_nov(), client, provider="demo", model="scripted")

    expected = (REPO_ROOT / "prompts" / "summary_system.md").read_text()
    assert [call["system"] for call in client.calls] == [expected, expected]
