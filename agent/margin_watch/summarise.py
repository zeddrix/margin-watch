"""The summary flow: facts -> model (tool-use loop) -> validator -> template on any failure.

Every provider (demo, local, Claude) goes through the same loop, the same system prompt and the
same validator. The model only writes words around strings that Python formatted.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from margin_watch.anthropic_client import DEFAULT_CLAUDE_MODEL, AnthropicClient
from margin_watch.config import REPO_ROOT
from margin_watch.demo_model import DEMO_MODEL, DemoModelClient
from margin_watch.facts import build_facts
from margin_watch.llm import (
    GET_JOB_FACTS,
    AssistantMessage,
    Message,
    ModelClient,
    ModelError,
    ToolCall,
    ToolResult,
    ToolResultsMessage,
    UserMessage,
)
from margin_watch.local_client import DEFAULT_LOCAL_MODEL, DEFAULT_LOCAL_URL, OpenAICompatibleClient
from margin_watch.models import Provider, RunReport, Summary
from margin_watch.template import template_summary
from margin_watch.validate import NumberCheck, allowed_tokens, check_numbers

SYSTEM_PROMPT_PATH = REPO_ROOT / "prompts" / "summary_system.md"
MAX_ROUNDS = 6
# Tests swap this for an httpx.MockTransport; None means a real network transport.
LOCAL_TRANSPORT: httpx.BaseTransport | None = None

_PROVIDERS: dict[str, Provider] = {
    "demo": "demo",
    "demo-bad": "demo-bad",
    "local": "local",
    "claude": "claude",
}


def load_system_prompt(path: Path = SYSTEM_PROMPT_PATH) -> str:
    return path.read_text(encoding="utf-8")


def facts_message(facts: dict[str, Any]) -> str:
    return (
        "Write today's morning margin summary.\n"
        "These are the overview facts as JSON. Call get_job_facts for each job in "
        "flagged_jobs, then write the summary using the numbers exactly as written.\n"
        f"<facts>{json.dumps(facts['overview'], ensure_ascii=False)}</facts>"
    )


def _run_tool(call: ToolCall, jobs: Mapping[str, Any]) -> ToolResult:
    if call.name != GET_JOB_FACTS.name:
        message = f"Unknown tool {call.name!r}. The only tool is {GET_JOB_FACTS.name}."
        return ToolResult(call.id, json.dumps({"error": message}), is_error=True)
    job_id = str(call.arguments.get("job_id", ""))
    if job_id not in jobs:
        message = f"No flagged job with id {job_id!r}. Flagged job ids: {', '.join(jobs)}."
        return ToolResult(call.id, json.dumps({"error": message}), is_error=True)
    return ToolResult(call.id, json.dumps(jobs[job_id], ensure_ascii=False))


def run_tool_loop(client: ModelClient, system: str, facts: dict[str, Any]) -> str:
    """Ask, answer tool calls, repeat; at most MAX_ROUNDS model calls. Returns the final text."""
    messages: list[Message] = [UserMessage(facts_message(facts))]
    for _ in range(MAX_ROUNDS):
        turn = client.complete(system, list(messages), [GET_JOB_FACTS])
        if turn.stop_reason == "refusal":
            raise ModelError("refusal")
        if turn.stop_reason == "max_tokens":
            raise ModelError("truncated")
        if not turn.tool_calls:
            if not (turn.text or "").strip():
                raise ModelError("empty_answer")
            return (turn.text or "").strip()
        messages.append(AssistantMessage(turn))
        results = tuple(_run_tool(call, facts["jobs"]) for call in turn.tool_calls)
        messages.append(ToolResultsMessage(results))
    raise ModelError("too_many_rounds")


def _template(
    report: RunReport,
    provider: Provider,
    model: str | None,
    reason: str,
    rejected: tuple[str, ...] = (),
) -> Summary:
    return Summary(
        text=template_summary(report.assessments, report.portfolio),
        source="template",
        provider=provider,
        model=model,
        fallback_reason=reason,
        rejected_tokens=rejected,
    )


@dataclass(frozen=True)
class SummaryOutcome:
    """The summary, plus what the model wrote and how each of its numbers checked out."""

    summary: Summary
    ai_text: str | None
    checks: tuple[NumberCheck, ...]


def summarise_detailed(
    report: RunReport, client: ModelClient, *, provider: Provider, model: str
) -> SummaryOutcome:
    """Run the tool-use loop and check every number; fall back to the template on any failure."""
    facts = build_facts(report)
    try:
        text = run_tool_loop(client, load_system_prompt(), facts)
    except ModelError as error:
        return SummaryOutcome(_template(report, provider, model, error.reason), None, ())
    checks = tuple(check_numbers(text, allowed_tokens(facts)))
    rejected = tuple(c.token for c in checks if not c.ok)
    if rejected:
        summary = _template(report, provider, model, "rejected_numbers", rejected)
    else:
        summary = Summary(
            text=text,
            source="ai_verified",
            provider=provider,
            model=model,
            fallback_reason=None,
        )
    return SummaryOutcome(summary, text, checks)


def summarise(report: RunReport, client: ModelClient, *, provider: Provider, model: str) -> Summary:
    """Run the tool-use loop and verify every number; fall back to the template on any failure."""
    return summarise_detailed(report, client, provider=provider, model=model).summary


def _setting(env: Mapping[str, str], key: str, default: str) -> str:
    return (env.get(key) or "").strip() or default


def _provider_and_model(ai: str, env: Mapping[str, str]) -> tuple[Provider, str]:
    if ai not in _PROVIDERS:
        raise ValueError(f"Unknown AI provider {ai!r}")
    if ai == "claude":
        return "claude", _setting(env, "MARGIN_WATCH_MODEL", DEFAULT_CLAUDE_MODEL)
    if ai == "local":
        return "local", _setting(env, "LOCAL_LLM_MODEL", DEFAULT_LOCAL_MODEL)
    return _PROVIDERS[ai], DEMO_MODEL


def create_client(ai: str, env: Mapping[str, str]) -> tuple[ModelClient, Provider, str]:
    """The client, provider name and model id for an `--ai` choice. Raises ModelError (no key)."""
    provider, model = _provider_and_model(ai, env)
    client: ModelClient
    if provider == "claude":
        client = AnthropicClient(model, api_key=(env.get("ANTHROPIC_API_KEY") or "").strip())
    elif provider == "local":
        url = _setting(env, "LOCAL_LLM_URL", DEFAULT_LOCAL_URL)
        client = OpenAICompatibleClient(url, model, transport=LOCAL_TRANSPORT)
    else:
        client = DemoModelClient(bad=provider == "demo-bad")
    return client, provider, model


def create_summary(report: RunReport, ai: str, env: Mapping[str, str]) -> Summary | None:
    """The summary for `--ai` choice `ai` (None for `off`, meaning the template)."""
    if ai == "off":
        return None
    provider, model = _provider_and_model(ai, env)
    try:
        client, _, _ = create_client(ai, env)
    except ModelError as error:
        return _template(report, provider, model, error.reason)
    return summarise(report, client, provider=provider, model=model)
