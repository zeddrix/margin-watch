"""The built-in scripted demo model: the real tool-use loop, offline and deterministic."""

from __future__ import annotations

from collections.abc import Sequence

from margin_watch.llm import Message, ModelTurn, ToolSpec

DEMO_MODEL = "demo-scripted-1"


class DemoModelClient:
    """Asks for each flagged job's facts, then writes sentences from the returned strings only.

    With `bad=True` (provider `demo-bad`) it slips in one invented figure, to show the validator
    rejecting it.
    """

    def __init__(self, bad: bool = False) -> None:
        self.bad = bad

    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn:
        raise NotImplementedError
