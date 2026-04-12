# Fitness Function 4: Graph Depth Limit (Circuit Breaker)
# Protege contra bucles infinitos - debe alcanzar HITL o éxito en X pasos

import pytest
from unittest.mock import AsyncMock
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


@pytest.mark.asyncio
async def test_circuit_breaker_triggers_at_max_depth():
    """Fitness: Graph reaches HITL within max steps when executor always fails."""
    max_expected_steps = 10

    executor = AlwaysFailingExecutor()
    step_count = 0

    initial_state = {
        "job_id": "fitness_test_4",
        "portal_name": "example",
        "profile_data": {},
        "job_data": {},
        "path_id": "test_cascade",
        "current_mission_id": "test",
        "current_state_id": "home",
        "current_url": "https://example.com",
        "dom_elements": [],
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "example",
        "patched_components": {},
    }

    config = {
        "configurable": {
            "thread_id": "fitness_test_4",
            "executor": executor,
            "motor_name": "crawl4ai",
            "record_graph": True,
        }
    }

    async with create_ariadne_graph(use_memory=True) as app:
        async for event in app.astream(initial_state, config, stream_mode="updates"):
            step_count += 1
            for node, state in event.items():
                if state.get("session_memory", {}).get("agent_failures", 0) >= 3:
                    break
            if step_count > max_expected_steps:
                break

    assert step_count <= max_expected_steps, (
        f"Graph exceeded max steps {max_expected_steps}: circuit breaker broken"
    )
    assert executor.call_count > 0, "Executor should have been called"
