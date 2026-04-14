"""Delphi — LLM cold-path rescue.

Activated when Theseus cannot identify the room or the Thread has no next step.
Receives raw HTML + screenshot from state["snapshot"] (ObserveNode already
captured the screenshot when agent_failures >= 1).

LLM call not yet implemented — see plan_docs/tasks/02-delphi-llm-implementation.md.
Circuit breaker is active: after MAX_FAILURES attempts the graph escalates to HITL.
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
        return {"agent_failures": failures}
