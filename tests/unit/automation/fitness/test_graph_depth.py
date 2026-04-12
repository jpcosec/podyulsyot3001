# Fitness Function 4: Graph Depth Limit (Circuit Breaker)
# Protege contra bucles infinitos - debe alcanzar HITL o éxito en X pasos

import pytest
from unittest.mock import AsyncMock, patch
from src.automation.ariadne.graph.orchestrator import create_ariadne_graph


class AlwaysFailingExecutor:
    """Executor that always fails to trigger circuit breaker."""

    def __init__(self):
        self.call_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def take_snapshot(self):
        from src.automation.ariadne.contracts.base import SnapshotResult

        return SnapshotResult(
            url="https://example.com", dom_elements=[], screenshot_b64="fake"
        )

    async def execute(self, command):
        self.call_count += 1
        from src.automation.ariadne.contracts.base import ExecutionResult

        return ExecutionResult(status="failed", error="Always fails for test")


@pytest.fixture
def mock_llm():
    """Mock LLM node to avoid API key requirement."""

    async def mock_node(state, config=None):
        mem = state.get("session_memory", {}).copy()
        mem["agent_failures"] = mem.get("agent_failures", 0) + 1
        return {"session_memory": mem, "errors": ["Mock LLM failed"]}

    from src.automation.ariadne.graph import orchestrator as orch_mod

    with patch.object(orch_mod, "llm_rescue_agent_node", mock_node):
        yield


@pytest.mark.asyncio
async def test_circuit_breaker_triggers_at_max_depth(mock_llm):
    """Fitness: Graph reaches HITL within max steps when executor always fails."""
    from src.automation.ariadne.graph.orchestrator import (
        create_ariadne_graph,
        route_after_deterministic_node,
    )

    max_expected_steps = 10
    step_count = 0

    # Create a state where all nodes fail
    state = {
        "job_id": "test_circuit",
        "portal_name": "fitness_test",
        "current_state_id": "start",
        "current_url": "https://example.com",
        "dom_elements": [],  # Empty - no targets found
        "session_memory": {},
        "errors": ["MapLoadError"],
        "history": [],
        "profile_data": {},
        "job_data": {},
    }

    config = {"configurable": {"thread_id": "test"}}

    async with create_ariadne_graph(use_memory=False) as app:
        # Simulate node failures until HITL
        for _ in range(15):
            result = await app.ainvoke(state, config)
            step_count += 1
            if result.get("session_memory", {}).get("agent_failures", 0) >= 3:
                break
            if step_count > max_expected_steps:
                break

    assert step_count <= max_expected_steps, (
        f"Circuit breaker failed: took {step_count} steps (max {max_expected_steps})"
    )
