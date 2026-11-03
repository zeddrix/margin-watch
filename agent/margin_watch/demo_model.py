"""The built-in scripted demo model: the real tool-use loop, offline and deterministic.

It is labelled "Demo AI" everywhere and is never presented as Claude. Its wording is scripted,
but it goes through the same loop and validator as a real model: first it asks for each flagged
job's facts, then it writes sentences that quote only the strings the tool returned.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

from margin_watch.llm import (
    Message,
    ModelTurn,
    ToolCall,
    ToolResultsMessage,
    ToolSpec,
    UserMessage,
)
from margin_watch.template import join_words
from margin_watch.validate import allowed_tokens

DEMO_MODEL = "demo-scripted-1"
# demo-bad slips in the first of these that isn't a real figure in today's facts.
_INVENTED = ("$13,750", "$21,400", "$9,875")


def _overview(messages: Sequence[Message]) -> dict[str, Any]:
    first = next(m for m in messages if isinstance(m, UserMessage))
    start = first.text.index("<facts>") + len("<facts>")
    end = first.text.index("</facts>")
    overview: dict[str, Any] = json.loads(first.text[start:end])
    return overview


def _job_facts(messages: Sequence[Message]) -> dict[str, dict[str, str]]:
    jobs: dict[str, dict[str, str]] = {}
    for message in messages:
        if isinstance(message, ToolResultsMessage):
            for result in message.results:
                if not result.is_error:
                    facts = json.loads(result.content)
                    jobs[facts["job_id"]] = facts
    return jobs


def _variant(job_id: str) -> int:
    """A stable choice between two phrasings (Python's hash() is salted per process)."""
    return int(hashlib.sha256(job_id.encode()).hexdigest(), 16) % 2


def _action_sentence(job: dict[str, str]) -> str:
    pm, name, job_id = job["project_manager"], job["name"], job["job_id"]
    forecast, quoted = job["forecast_margin"], job["quoted_margin"]
    driver = job.get("main_driver")
    overrun = job.get("main_driver_overrun")
    loss = job["status"] == "LOSS"
    state = "heading for a loss" if loss else "at risk"
    if _variant(job_id) == 0:
        lead = (
            f"Call {pm} today about {name} ({job_id})"
            if loss
            else f"Ring {pm} about {name} ({job_id})"
        )
        tail = f" and {driver} {overrun} over estimate" if driver and overrun else ""
        return (
            f"{lead}: it is {state}, with forecast margin at {forecast} "
            f"against {quoted} quoted{tail}."
        )
    lead = (
        f"{pm} needs a call today about {name} ({job_id})"
        if loss
        else (f"{pm} should look at {name} ({job_id}) today")
    )
    tail = f", mostly from {driver} running {overrun} over estimate" if driver and overrun else ""
    return f"{lead}, which is {state} at {forecast} forecast margin against {quoted} quoted{tail}."


def _listing(jobs: list[dict[str, str]]) -> str:
    return join_words([f"{j['name']} ({j['job_id']}, {j['project_manager']})" for j in jobs])


def _summary(overview: dict[str, Any], jobs: dict[str, dict[str, str]], bad: bool) -> str:
    ordered = [jobs[f["job_id"]] for f in overview["flagged_jobs"] if f["job_id"] in jobs]
    action = [j for j in ordered if j["status"] in ("LOSS", "AT_RISK")]
    watch = [j for j in ordered if j["status"] == "WATCH"]
    review = [j for j in ordered if j["status"] == "NEEDS_REVIEW"]

    sentences = [_action_sentence(j) for j in action[:3]]
    if action[3:]:
        sentences.append(f"Also needing a call today: {_listing(action[3:])}.")
    if watch:
        verb = "is" if len(watch) == 1 else "are"
        sentences.append(f"Keep an eye on {_listing(watch)}, which {verb} on watch.")
    if review:
        names = join_words([f"{j['name']} ({j['job_id']})" for j in review])
        subject = "it was" if len(review) == 1 else "they were"
        sentences.append(
            f"Check Simpro before trusting {names}: the job data is incomplete or wrong, "
            f"so {subject} not assessed."
        )
    needing = overview["jobs_needing_action"]
    if action:
        jobs_word = "job needs" if needing == "1" else "jobs need"
        sentences.append(
            f"In total, {needing} {jobs_word} action today and forecast overruns add up to "
            f"{overview['total_dollars_at_risk']}."
        )
    elif not ordered:
        sentences.append("Every job is on track today, so nothing needs a call.")

    if bad:
        real = allowed_tokens([overview, list(jobs.values())])
        invented = next(v for v in _INVENTED if v not in real)
        sentences.insert(1, f"That is about {invented} more than the original budget.")
    return " ".join(sentences)


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
        overview = _overview(messages)
        if not any(isinstance(m, ToolResultsMessage) for m in messages):
            calls = tuple(
                ToolCall(id=f"demo_{i}", name="get_job_facts", arguments={"job_id": f["job_id"]})
                for i, f in enumerate(overview["flagged_jobs"], start=1)
            )
            if calls:
                return ModelTurn(text=None, tool_calls=calls, stop_reason="tool_use")
        return ModelTurn(text=_summary(overview, _job_facts(messages), self.bad))
