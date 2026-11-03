"""`OpenAICompatibleClient`: a local server such as LM Studio (`/v1/chat/completions`)."""

from __future__ import annotations

from collections.abc import Sequence

import httpx

from margin_watch.llm import Message, ModelTurn, ToolSpec

DEFAULT_LOCAL_URL = "http://localhost:1234"
DEFAULT_LOCAL_MODEL = "local-model"
TIMEOUT_SECONDS = 30.0
MAX_TOKENS = 500


class OpenAICompatibleClient:
    def __init__(
        self,
        base_url: str = DEFAULT_LOCAL_URL,
        model: str = DEFAULT_LOCAL_MODEL,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        raise NotImplementedError

    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn:
        raise NotImplementedError
