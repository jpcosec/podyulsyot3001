"""Delphi — LLM cold-path rescue.

Activated when Theseus cannot identify the room or the Thread has no next step.
Receives raw HTML + screenshot from state["snapshot"] (ObserveNode already
captured the screenshot when agent_failures >= 1).

Status: stub — wired into the graph but not yet implemented.
"""

from __future__ import annotations

from src.automation.contracts.state import AriadneState

MAX_FAILURES = 5


class DelphiNode:

    async def __call__(self, state: AriadneState) -> dict:
        failures = state.get("agent_failures", 0) + 1
        if failures >= MAX_FAILURES:
            return {
                "agent_failures": failures,
                "errors": ["DelphiError: circuit breaker exhausted — escalating to HITL"],
            }
        # TODO: LLM call with state["snapshot"].html + state["snapshot"].screenshot_b64
        return {
            "agent_failures": failures,
            "errors": [f"DelphiError: not yet implemented (attempt {failures}/{MAX_FAILURES})"],
        }
