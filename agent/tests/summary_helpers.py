"""Helpers for Phase 5 tests: sample reports and fake model clients that behave like real ones."""

from __future__ import annotations

import copy
from datetime import date, datetime
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

from conftest import DEFAULT_THRESHOLDS, SAMPLE_3_NOV, SAMPLE_4_NOV

from margin_watch.llm import ModelTurn, ToolCall
from margin_watch.run import build_report
from margin_watch.sources import SampleFileSource

MELBOURNE = ZoneInfo("Australia/Melbourne")
VALID_ANSWER = (
    "Call Dave Kowalski today about 1042: forecast margin is -2.5% against 17.5% quoted. "
    "Labour is $12,000 over estimate. 3 jobs need action."
)


def report_4_nov():
    return build_report(
        SampleFileSource(SAMPLE_4_NOV).load(),
        source_name=SAMPLE_4_NOV.name,
        as_of=date(2026, 11, 4),
        generated_at=datetime(2026, 11, 4, 6, 30, tzinfo=MELBOURNE),
        thresholds=DEFAULT_THRESHOLDS,
    )


def report_3_nov():
    return build_report(
        SampleFileSource(SAMPLE_3_NOV).load(),
        source_name=SAMPLE_3_NOV.name,
        as_of=date(2026, 11, 3),
        generated_at=datetime(2026, 11, 3, 6, 30, tzinfo=MELBOURNE),
        thresholds=DEFAULT_THRESHOLDS,
    )


class ScriptedClient:
    """A ModelClient that replays turns and records every call."""

    def __init__(self, *turns: ModelTurn) -> None:
        self.turns = list(turns)
        self.calls: list[dict[str, Any]] = []

    def complete(self, system, messages, tools):
        self.calls.append({"system": system, "messages": list(messages), "tools": list(tools)})
        return self.turns.pop(0)


def tool_turn(*job_ids: str, name: str = "get_job_facts") -> ModelTurn:
    calls = tuple(ToolCall(id=f"call_{i}", name=name, arguments={"job_id": j})
                  for i, j in enumerate(job_ids, start=1))  # fmt: skip
    return ModelTurn(text=None, tool_calls=calls, stop_reason="tool_use")


def text_turn(text: str) -> ModelTurn:
    return ModelTurn(text=text, stop_reason="end_turn")


# --- fake Anthropic SDK (same attribute shapes as anthropic.types.Message) -----------------------


def sdk_tool_use(*job_ids: str) -> SimpleNamespace:
    blocks = [
        SimpleNamespace(type="tool_use", id=f"toolu_{i}", name="get_job_facts", input={"job_id": j})
        for i, j in enumerate(job_ids, start=1)
    ]
    return SimpleNamespace(content=blocks, stop_reason="tool_use")


def sdk_text(text: str, stop_reason: str = "end_turn") -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)], stop_reason=stop_reason
    )


class FakeMessages:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(copy.copy(kwargs) | {"messages": list(kwargs["messages"])})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeAnthropicSDK:
    def __init__(self, *responses: Any) -> None:
        self.messages = FakeMessages(list(responses))
