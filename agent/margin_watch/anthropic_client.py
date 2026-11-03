"""`AnthropicClient`: the Messages API with tool use. Never called for real in this build.

Request: model (default claude-sonnet-5-5), the shared system prompt, one tool, max_tokens 500.
Claude Sonnet 5.5 rejects non-default sampling and `thinking: disabled`, so there is no
`temperature`, and `thinking: between_tools` keeps the 500 tokens for the answer
(docs/decisions.md). Determinism comes from the validator, not from sampling settings.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import anthropic

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

DEFAULT_CLAUDE_MODEL = "claude-sonnet-5-5"
TIMEOUT_SECONDS = 20.0
MAX_TOKENS = 500


def _assistant_content(message: AssistantMessage) -> Any:
    turn = message.turn
    if turn.raw is not None:
        return turn.raw  # echo the response content unchanged (keeps any thinking blocks valid)
    blocks: list[dict[str, Any]] = []
    if turn.text:
        blocks.append({"type": "text", "text": turn.text})
    blocks.extend(
        {"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments}
        for c in turn.tool_calls
    )
    return blocks


def _wire(messages: Sequence[Message]) -> list[dict[str, Any]]:
    wire: list[dict[str, Any]] = []
    for message in messages:
        if isinstance(message, UserMessage):
            wire.append({"role": "user", "content": message.text})
        elif isinstance(message, AssistantMessage):
            wire.append({"role": "assistant", "content": _assistant_content(message)})
        elif isinstance(message, ToolResultsMessage):
            results: list[dict[str, Any]] = []
            for result in message.results:
                block: dict[str, Any] = {
                    "type": "tool_result",
                    "tool_use_id": result.tool_call_id,
                    "content": result.content,
                }
                if result.is_error:
                    block["is_error"] = True
                results.append(block)
            wire.append({"role": "user", "content": results})
    return wire


class AnthropicClient:
    def __init__(
        self, model: str = DEFAULT_CLAUDE_MODEL, *, api_key: str | None = None, sdk: Any = None
    ) -> None:
        self.model = model
        if sdk is None:
            if not api_key:
                raise ModelError("no_api_key")
            sdk = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=1)
        self.sdk = sdk

    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn:
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": system,
            "tools": [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in tools
            ],
            "messages": _wire(messages),
        }
        if self.model == DEFAULT_CLAUDE_MODEL:
            request["thinking"] = {"type": "between_tools"}
        try:
            response = self.sdk.messages.create(**request)
        except anthropic.APITimeoutError as error:  # subclass of APIConnectionError: check first
            raise ModelError("timeout", str(error)) from error
        except anthropic.APIConnectionError as error:
            raise ModelError("unreachable", str(error)) from error
        except anthropic.RateLimitError as error:
            raise ModelError("rate_limited", str(error)) from error
        except anthropic.AuthenticationError as error:
            raise ModelError("auth_error", str(error)) from error
        except anthropic.APIStatusError as error:
            raise ModelError("api_error", f"HTTP {error.status_code}") from error

        texts: list[str] = []
        calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                texts.append(block.text)
            elif block.type == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name, arguments=dict(block.input)))
        return ModelTurn(
            text="".join(texts) or None,
            tool_calls=tuple(calls),
            stop_reason=str(response.stop_reason),
            raw=response.content,
        )
