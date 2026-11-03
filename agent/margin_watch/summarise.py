"""The summary flow: facts -> model (tool-use loop) -> validator -> template on any failure."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import httpx

from margin_watch.config import REPO_ROOT
from margin_watch.llm import ModelClient
from margin_watch.models import Provider, RunReport, Summary

SYSTEM_PROMPT_PATH = REPO_ROOT / "prompts" / "summary_system.md"
MAX_ROUNDS = 6
# Tests swap this for an httpx.MockTransport; None means a real network transport.
LOCAL_TRANSPORT: httpx.BaseTransport | None = None


def load_system_prompt(path: Path = SYSTEM_PROMPT_PATH) -> str:
    raise NotImplementedError


def summarise(report: RunReport, client: ModelClient, *, provider: Provider, model: str) -> Summary:
    """Run the tool-use loop and verify every number; fall back to the template on any failure."""
    raise NotImplementedError


def create_summary(report: RunReport, ai: str, env: Mapping[str, str]) -> Summary | None:
    """The summary for `--ai` choice `ai` (None for `off`, meaning the template)."""
    raise NotImplementedError


def create_client(ai: str, env: Mapping[str, str]) -> tuple[ModelClient, Provider, str]:
    """The client, provider name and model id for an `--ai` choice. Raises ModelError (no key)."""
    raise NotImplementedError
