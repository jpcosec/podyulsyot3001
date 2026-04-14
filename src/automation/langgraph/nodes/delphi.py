"""Delphi — LLM cold-path rescue.

Activated when Theseus cannot identify the room or the Thread has no next step.
Receives HTML + optional screenshot from state["snapshot"] and calls the LLM
to propose a MotorCommand. Executes it, appends the TraceEvent.

Circuit breaker: after MAX_FAILURES attempts the graph escalates to HITL.
HITL is signalled by "HITLRequired:" prefix in state["errors"].
"""

from __future__ import annotations

import json
import re

from src.automation.contracts.motor import Motor, MotorCommand
from src.automation.contracts.llm import LLMClient
from src.automation.contracts.state import AriadneState
from src.automation.ariadne.labyrinth.labyrinth import Labyrinth

MAX_FAILURES = 5

_COMMAND_SCHEMA = '{"operation": "click|fill|navigate|scroll", "selector": "css", "value": "optional"}'


class DelphiNode:

    def __init__(self, motor: Motor, labyrinth: Labyrinth, llm: LLMClient) -> None:
        self._motor = motor
        self._labyrinth = labyrinth
        self._llm = llm

    async def __call__(self, state: AriadneState) -> dict:
        failures = state.get("agent_failures", 0) + 1
        if failures >= MAX_FAILURES:
            return _hitl_patch(failures)
        snapshot = state.get("snapshot")
        if not snapshot:
            return _error_patch(failures, "DelphiError: no snapshot in state")
        command = await self._reason(snapshot, state)
        if not command:
            return _error_patch(failures, "DelphiError: LLM returned no parseable command")
        return await self._execute(command, failures)

    async def _reason(self, snapshot, state) -> MotorCommand | None:
        dead_ends = self._labyrinth.known_dead_ends()
        prompt = _build_prompt(snapshot, state.get("current_room_id"), dead_ends)
        response = await self._llm.complete(prompt, snapshot.screenshot_b64)
        return _parse_command(response)

    async def _execute(self, command: MotorCommand, failures: int) -> dict:
        result = await self._motor.act(command)
        trace = [result.trace_event]
        if not result.success:
            error = result.error or "DelphiError: command failed"
            return {"agent_failures": failures, "trace": trace, "errors": [error]}
        return {"agent_failures": failures, "trace": trace}


# ── Module-level helpers ──────────────────────────────────────────────────────

def _hitl_patch(failures: int) -> dict:
    return {"agent_failures": failures, "errors": ["HITLRequired: circuit breaker exhausted"]}


def _error_patch(failures: int, msg: str) -> dict:
    return {"agent_failures": failures, "errors": [msg]}


def _build_prompt(snapshot, room_id: str | None, dead_ends: list[str]) -> str:
    room_ctx = f"Current room: {room_id}" if room_id else "Current room: unknown"
    dead_ctx = f"Avoid rooms: {', '.join(dead_ends)}" if dead_ends else ""
    html_excerpt = snapshot.html[:3000]
    return (
        f"You are a web automation agent.\n"
        f"URL: {snapshot.url}\n{room_ctx}\n{dead_ctx}\n\n"
        f"HTML:\n{html_excerpt}\n\n"
        f"Propose ONE command to advance the mission.\n"
        f"Reply with ONLY valid JSON: {_COMMAND_SCHEMA}"
    )


def _parse_command(response: str) -> MotorCommand | None:
    try:
        match = re.search(r'\{[^{}]+\}', response, re.DOTALL)
        data = json.loads(match.group())
        return MotorCommand(
            operation=data["operation"],
            selector=data.get("selector", ""),
            value=data.get("value"),
        )
    except Exception:
        return None
