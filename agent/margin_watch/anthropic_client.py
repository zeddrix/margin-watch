"""`AnthropicClient`: the Messages API with tool use. Never called for real in this build."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from margin_watch.llm import Message, ModelTurn, ToolSpec

DEFAULT_CLAUDE_MODEL = "claude-sonnet-5-5"
TIMEOUT_SECONDS = 20.0
MAX_TOKENS = 500


class AnthropicClient:
    def __init__(
        self, model: str = DEFAULT_CLAUDE_MODEL, *, api_key: str | None = None, sdk: Any = None
    ) -> None:
        raise NotImplementedError

    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn:
        raise NotImplementedError
