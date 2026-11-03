"""Provider-neutral model types and the one tool. Each client translates to its own wire format."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


GET_JOB_FACTS = ToolSpec(
    name="get_job_facts",
    description=(
        "Get the pre-formatted facts for one flagged job: status, PM, margins, dollars at risk "
        "and main cost driver. Every number is a string to be used exactly as written."
    ),
    input_schema={
        "type": "object",
        "properties": {"job_id": {"type": "string", "description": 'Job id, e.g. "1042".'}},
        "required": ["job_id"],
        "additionalProperties": False,
    },
)


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass(frozen=True)
class ModelTurn:
    """One model reply: text, tool calls, or both. `raw` is the provider's own content to echo."""

    text: str | None
    tool_calls: tuple[ToolCall, ...] = ()
    stop_reason: str = "end_turn"
    raw: Any = field(default=None, compare=False)


@dataclass(frozen=True)
class UserMessage:
    text: str


@dataclass(frozen=True)
class AssistantMessage:
    turn: ModelTurn


@dataclass(frozen=True)
class ToolResultsMessage:
    results: tuple[ToolResult, ...]


Message = UserMessage | AssistantMessage | ToolResultsMessage


class ModelError(Exception):
    """A model call failed. `reason` becomes the summary's fallback_reason."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


class ModelClient(Protocol):
    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn: ...
