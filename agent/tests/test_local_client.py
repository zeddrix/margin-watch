"""OpenAICompatibleClient with httpx.MockTransport (AC-66, AC-67)."""

import json

import httpx
import pytest
from summary_helpers import VALID_ANSWER, report_4_nov

from margin_watch.config import REPO_ROOT
from margin_watch.local_client import OpenAICompatibleClient
from margin_watch.summarise import create_client, summarise

URL = "http://localhost:1234"


def _tool_reply(*job_ids):
    calls = [
        {"id": f"call_{i}", "type": "function",
         "function": {"name": "get_job_facts", "arguments": json.dumps({"job_id": j})}}
        for i, j in enumerate(job_ids, start=1)
    ]  # fmt: skip
    return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": calls},
                         "finish_reason": "tool_calls"}]}  # fmt: skip


def _text_reply(text):
    return {"choices": [{"message": {"role": "assistant", "content": text},
                         "finish_reason": "stop"}]}  # fmt: skip


class Recorder:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, httpx.Response):
            return reply
        return httpx.Response(200, json=reply)


def _run(recorder):
    client = OpenAICompatibleClient(URL, "qwen-test", transport=httpx.MockTransport(recorder))
    return summarise(report_4_nov(), client, provider="local", model="qwen-test")


def test_ac66_request_shape():
    """AC-66: POST /v1/chat/completions with model, system + facts, function tool, 500, temp 0."""
    recorder = Recorder(_tool_reply("1042"), _text_reply(VALID_ANSWER))

    _run(recorder)

    request = recorder.requests[0]
    body = json.loads(request.content)
    assert request.method == "POST"
    assert str(request.url) == f"{URL}/v1/chat/completions"
    assert body["model"] == "qwen-test"
    assert body["max_tokens"] == 500
    assert body["temperature"] == 0
    assert body["messages"][0] == {
        "role": "system",
        "content": (REPO_ROOT / "prompts" / "summary_system.md").read_text(),
    }
    assert body["messages"][1]["role"] == "user"
    assert "<facts>" in body["messages"][1]["content"]
    assert len(body["tools"]) == 1
    assert body["tools"][0]["type"] == "function"
    assert body["tools"][0]["function"]["name"] == "get_job_facts"
    assert body["tools"][0]["function"]["parameters"]["required"] == ["job_id"]


def test_ac66_tool_calls_round_trip():
    """AC-66: JSON-string arguments parsed; follow-up sends assistant tool_calls and
    tool messages."""
    recorder = Recorder(_tool_reply("1042", "1038"), _text_reply(VALID_ANSWER))

    summary = _run(recorder)

    second = json.loads(recorder.requests[1].content)["messages"]
    assistant = second[2]
    assert assistant["role"] == "assistant"
    assert [c["id"] for c in assistant["tool_calls"]] == ["call_1", "call_2"]
    assert json.loads(assistant["tool_calls"][0]["function"]["arguments"]) == {"job_id": "1042"}
    tools = second[3:]
    assert [m["role"] for m in tools] == ["tool", "tool"]
    assert [m["tool_call_id"] for m in tools] == ["call_1", "call_2"]
    assert json.loads(tools[0]["content"])["dollars_at_risk"] == "$16,000"
    assert summary.source == "ai_verified"
    assert summary.provider == "local"


@pytest.mark.parametrize(
    ("reply", "reason"),
    [
        (httpx.ConnectError("connection refused"), "unreachable"),
        (httpx.ReadTimeout("timed out"), "timeout"),
        (httpx.Response(500, text="server error"), "api_error"),
        (httpx.Response(200, text="<html>not json</html>"), "bad_response"),
        (httpx.Response(200, json={"choices": []}), "bad_response"),
    ],
    ids=["connect", "timeout", "http-500", "not-json", "no-choices"],
)
def test_ac67_failures_fall_back(reply, reason):
    """AC-67: connection, timeout, HTTP and shape failures -> template with the right reason."""
    summary = _run(Recorder(reply))

    assert summary.source == "template"
    assert summary.provider == "local"
    assert summary.fallback_reason == reason


def test_ac67_client_from_env_uses_thirty_second_timeout():
    """AC-67: LOCAL_LLM_URL / LOCAL_LLM_MODEL configure the client; timeout is 30 s."""
    client, provider, model = create_client(
        "local", {"LOCAL_LLM_URL": "http://127.0.0.1:5555", "LOCAL_LLM_MODEL": "llama-local"}
    )

    assert isinstance(client, OpenAICompatibleClient)
    assert provider == "local"
    assert model == "llama-local"
    assert client.timeout == 30.0
    assert client.base_url == "http://127.0.0.1:5555"
