"""AnthropicClient with a fake SDK client: request shape, parsing, fallbacks (AC-64, AC-65)."""

import anthropic
import httpx2
import pytest
from summary_helpers import (
    VALID_ANSWER,
    FakeAnthropicSDK,
    report_4_nov,
    sdk_text,
    sdk_tool_use,
)

from margin_watch.anthropic_client import AnthropicClient
from margin_watch.config import REPO_ROOT
from margin_watch.summarise import create_client, create_summary, summarise
from margin_watch.template import template_summary

REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def _run(sdk, model="claude-sonnet-5-5"):
    return summarise(
        report_4_nov(), AnthropicClient(model, sdk=sdk), provider="claude", model=model
    )


def test_ac64_request_shape():
    """AC-64: model, system prompt, one tool, max_tokens 500, between_tools thinking,
    no temperature."""
    sdk = FakeAnthropicSDK(sdk_tool_use("1042"), sdk_text(VALID_ANSWER))

    _run(sdk)

    first = sdk.messages.calls[0]
    assert first["model"] == "claude-sonnet-5-5"
    assert first["system"] == (REPO_ROOT / "prompts" / "summary_system.md").read_text()
    assert first["max_tokens"] == 500
    assert first["thinking"] == {"type": "between_tools"}
    assert "temperature" not in first
    assert len(first["tools"]) == 1
    tool = first["tools"][0]
    assert set(tool) == {"name", "description", "input_schema"}
    assert tool["name"] == "get_job_facts"
    assert tool["input_schema"]["required"] == ["job_id"]
    assert tool["input_schema"]["properties"]["job_id"]["type"] == "string"
    assert first["messages"][0]["role"] == "user"
    assert "<facts>" in first["messages"][0]["content"]


def test_ac64_follow_up_echoes_content_and_sends_tool_results():
    """AC-64: the follow-up echoes the assistant content and sends matching tool_result blocks."""
    tool_response = sdk_tool_use("1042", "1038")
    sdk = FakeAnthropicSDK(tool_response, sdk_text(VALID_ANSWER))

    summary = _run(sdk)

    second = sdk.messages.calls[1]["messages"]
    assert second[1] == {"role": "assistant", "content": tool_response.content}
    assert second[2]["role"] == "user"
    results = second[2]["content"]
    assert [r["type"] for r in results] == ["tool_result", "tool_result"]
    assert [r["tool_use_id"] for r in results] == ["toolu_1", "toolu_2"]
    assert '"$16,000"' in results[0]["content"]
    assert summary.source == "ai_verified"
    assert summary.provider == "claude"
    assert summary.text == VALID_ANSWER


def test_ac64_model_comes_from_env():
    """AC-64: MARGIN_WATCH_MODEL picks the Claude model; the default is claude-sonnet-5-5."""
    _, provider, model = create_client("claude", {"ANTHROPIC_API_KEY": "test-key"})
    _, _, custom = create_client(
        "claude", {"ANTHROPIC_API_KEY": "test-key", "MARGIN_WATCH_MODEL": "claude-opus-5-5"}
    )

    assert provider == "claude"
    assert model == "claude-sonnet-5-5"
    assert custom == "claude-opus-5-5"


def test_ac65_no_api_key_uses_template_without_error():
    """AC-65: no ANTHROPIC_API_KEY -> template, fallback 'no_api_key', no exception."""
    report = report_4_nov()

    summary = create_summary(report, "claude", {})

    assert summary is not None
    assert summary.source == "template"
    assert summary.provider == "claude"
    assert summary.fallback_reason == "no_api_key"
    assert summary.text == template_summary(report.assessments, report.portfolio)


def test_ac65_real_client_uses_twenty_second_timeout():
    """AC-65: a client built from a key uses a 20 s timeout (no request is made)."""
    client, _, _ = create_client("claude", {"ANTHROPIC_API_KEY": "test-key"})

    assert isinstance(client, AnthropicClient)
    assert client.sdk.timeout == 20.0


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (anthropic.APITimeoutError(request=REQUEST), "timeout"),
        (anthropic.APIConnectionError(request=REQUEST), "unreachable"),
        (
            anthropic.RateLimitError(
                "slow down", response=httpx2.Response(429, request=REQUEST), body=None
            ),
            "rate_limited",
        ),
        (
            anthropic.InternalServerError(
                "boom", response=httpx2.Response(500, request=REQUEST), body=None
            ),
            "api_error",
        ),
    ],
    ids=["timeout", "connection", "rate-limit", "server-error"],
)
def test_ac65_sdk_errors_fall_back(error, reason):
    """AC-65: SDK exceptions map to fallback reasons and the template."""
    summary = _run(FakeAnthropicSDK(error))

    assert summary.source == "template"
    assert summary.fallback_reason == reason


@pytest.mark.parametrize(("stop_reason", "reason"), [("refusal", "refusal"),
                                                      ("max_tokens", "truncated")])  # fmt: skip
def test_ac65_refusal_and_truncation_fall_back(stop_reason, reason):
    """AC-65: stop_reason refusal -> 'refusal'; max_tokens -> 'truncated'."""
    summary = _run(FakeAnthropicSDK(sdk_tool_use("1042"), sdk_text(VALID_ANSWER, stop_reason)))

    assert summary.source == "template"
    assert summary.fallback_reason == reason
