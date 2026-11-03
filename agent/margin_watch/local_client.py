"""`OpenAICompatibleClient`: a local server such as LM Studio (`/v1/chat/completions`).

Never called for real in this build; tests use `httpx.MockTransport`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

import httpx

from margin_watch.llm import (
    AssistantMessage,
    Message,
    ModelError,
    ModelTurn,
    ToolCall,
    ToolResultsMessage,
    ToolSpec,
    UserMessage,
)

DEFAULT_LOCAL_URL = "http://localhost:1234"
DEFAULT_LOCAL_MODEL = "local-model"
TIMEOUT_SECONDS = 30.0
MAX_TOKENS = 500
_STOP_REASONS = {"length": "max_tokens", "tool_calls": "tool_use", "content_filter": "refusal"}


def _wire(system: str, messages: Sequence[Message]) -> list[dict[str, Any]]:
    wire: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for message in messages:
        if isinstance(message, UserMessage):
            wire.append({"role": "user", "content": message.text})
        elif isinstance(message, AssistantMessage):
            entry: dict[str, Any] = {"role": "assistant", "content": message.turn.text}
            if message.turn.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": c.id,
                        "type": "function",
                        "function": {"name": c.name, "arguments": json.dumps(c.arguments)},
                    }
                    for c in message.turn.tool_calls
                ]
            wire.append(entry)
        elif isinstance(message, ToolResultsMessage):
            wire.extend(
                {"role": "tool", "tool_call_id": r.tool_call_id, "content": r.content}
                for r in message.results
            )
    return wire


def _parse(data: Any) -> ModelTurn:
    try:
        choice = data["choices"][0]
        message = choice["message"]
        calls = tuple(
            ToolCall(
                id=str(call["id"]),
                name=str(call["function"]["name"]),
                arguments=dict(json.loads(call["function"]["arguments"] or "{}")),
            )
            for call in message.get("tool_calls") or []
        )
        content = message.get("content")
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ModelError("bad_response", f"unexpected reply shape: {error}") from error
    finish = str(choice.get("finish_reason") or "stop")
    return ModelTurn(
        text=content if isinstance(content, str) else None,
        tool_calls=calls,
        stop_reason=_STOP_REASONS.get(finish, "end_turn"),
    )


class OpenAICompatibleClient:
    def __init__(
        self,
        base_url: str = DEFAULT_LOCAL_URL,
        model: str = DEFAULT_LOCAL_MODEL,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = TIMEOUT_SECONDS
        self._http = httpx.Client(base_url=self.base_url, timeout=self.timeout, transport=transport)

    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn:
        body = {
            "model": self.model,
            "messages": _wire(system, messages),
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.input_schema,
                    },
                }
                for t in tools
            ],
            "max_tokens": MAX_TOKENS,
            "temperature": 0,
        }
        try:
            response = self._http.post("/v1/chat/completions", json=body)
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise ModelError("timeout", str(error)) from error
        except httpx.TransportError as error:
            raise ModelError("unreachable", str(error)) from error
        except httpx.HTTPStatusError as error:
            raise ModelError("api_error", f"HTTP {error.response.status_code}") from error
        try:
            data = response.json()
        except ValueError as error:
            raise ModelError("bad_response", "reply isn't JSON") from error
        return _parse(data)
