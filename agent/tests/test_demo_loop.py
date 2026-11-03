"""Demo model and the shared tool-use loop (AC-58..AC-63)."""

import json
import re

from summary_helpers import (
    VALID_ANSWER,
    ScriptedClient,
    report_3_nov,
    report_4_nov,
    text_turn,
    tool_turn,
)

from margin_watch.demo_model import DemoModelClient
from margin_watch.facts import build_facts
from margin_watch.llm import GET_JOB_FACTS, ToolResultsMessage, UserMessage
from margin_watch.summarise import load_system_prompt, summarise
from margin_watch.template import template_summary
from margin_watch.validate import allowed_tokens, validate_text

FLAGGED_4_NOV = ["1042", "1038", "1035", "1033", "1040", "1039", "1044"]


def _facts_message(report):
    facts = build_facts(report)
    return UserMessage(text="Facts:\n<facts>" + json.dumps(facts["overview"]) + "</facts>")


def _template(report):
    return template_summary(report.assessments, report.portfolio)


def test_ac58_demo_requests_facts_for_each_flagged_job_first():
    """AC-58: the demo's first turn is one get_job_facts call per flagged job, in risk order."""
    turn = DemoModelClient().complete(
        load_system_prompt(), [_facts_message(report_4_nov())], [GET_JOB_FACTS]
    )

    assert not turn.text
    assert [c.name for c in turn.tool_calls] == ["get_job_facts"] * 7
    assert [c.arguments["job_id"] for c in turn.tool_calls] == FLAGGED_4_NOV
    assert len({c.id for c in turn.tool_calls}) == 7


def test_ac59_demo_summary_is_verified_and_deterministic():
    """AC-59: demo -> ai_verified, 3-6 sentences, leads with Dave Kowalski / 1042, deterministic."""
    report = report_4_nov()

    first = summarise(report, DemoModelClient(), provider="demo", model="demo-scripted-1")
    second = summarise(report, DemoModelClient(), provider="demo", model="demo-scripted-1")

    assert first.source == "ai_verified"
    assert first.provider == "demo"
    assert first.model == "demo-scripted-1"
    assert first.fallback_reason is None
    assert first.rejected_tokens == ()
    assert first.text == second.text
    assert first.text != _template(report)
    sentences = re.findall(r"[.!?](?:\s|$)", first.text)
    assert 3 <= len(sentences) <= 6
    opening = re.split(r"(?<=[.!?])\s", first.text)[0]
    assert "Dave Kowalski" in opening
    assert "1042" in opening
    assert validate_text(first.text, allowed_tokens(build_facts(report))).ok


def test_ac59_demo_summary_verified_on_3_nov():
    """AC-59: the 3 Nov demo summary is verified too."""
    summary = summarise(report_3_nov(), DemoModelClient(), provider="demo", model="demo-scripted-1")

    assert summary.source == "ai_verified"


def test_ac60_demo_bad_is_rejected_on_both_dates():
    """AC-60: demo-bad's invented '$13,750' is rejected and the template is used."""
    for report in (report_4_nov(), report_3_nov()):
        summary = summarise(
            report, DemoModelClient(bad=True), provider="demo-bad", model="demo-scripted-1"
        )

        assert summary.source == "template"
        assert summary.provider == "demo-bad"
        assert summary.text == _template(report)
        assert summary.rejected_tokens == ("$13,750",)
        assert summary.fallback_reason == "rejected_numbers"


def test_ac61_unknown_job_id_is_a_tool_error_and_loop_continues():
    """AC-61: get_job_facts('9999') -> error tool result naming 9999; then a valid answer wins."""
    client = ScriptedClient(tool_turn("9999"), tool_turn("1042"), text_turn(VALID_ANSWER))

    summary = summarise(report_4_nov(), client, provider="demo", model="scripted")

    results = client.calls[1]["messages"][-1]
    assert isinstance(results, ToolResultsMessage)
    assert results.results[0].is_error is True
    assert "9999" in results.results[0].content
    good = client.calls[2]["messages"][-1].results[0]
    assert good.is_error is False
    assert json.loads(good.content)["dollars_at_risk"] == "$16,000"
    assert summary.source == "ai_verified"
    assert summary.text == VALID_ANSWER


def test_ac61_unknown_tool_name_is_a_tool_error():
    """AC-61: an unknown tool name also gets an error result, not a crash."""
    client = ScriptedClient(tool_turn("1042", name="delete_job"), text_turn(VALID_ANSWER))

    summary = summarise(report_4_nov(), client, provider="demo", model="scripted")

    result = client.calls[1]["messages"][-1].results[0]
    assert result.is_error is True
    assert "delete_job" in result.content
    assert summary.source == "ai_verified"


def test_ac62_loop_stops_after_six_rounds():
    """AC-62: a model that always calls a tool is called exactly 6 times, then template."""
    client = ScriptedClient(*[tool_turn("1042") for _ in range(10)])
    report = report_4_nov()

    summary = summarise(report, client, provider="demo", model="scripted")

    assert len(client.calls) == 6
    assert summary.source == "template"
    assert summary.fallback_reason == "too_many_rounds"
    assert summary.text == _template(report)


def test_ac63_empty_answer_falls_back():
    """AC-63: an empty or whitespace final answer -> template, fallback 'empty_answer'."""
    for empty in ("", "   \n"):
        client = ScriptedClient(tool_turn("1042"), text_turn(empty))

        summary = summarise(report_4_nov(), client, provider="demo", model="scripted")

        assert summary.source == "template"
        assert summary.fallback_reason == "empty_answer"
