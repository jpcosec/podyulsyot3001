"""Fitness Function 4: Graph Depth / Circuit Breaker.

Validates that the real Ariadne graph reaches human-in-the-loop within a
bounded number of steps when deterministic execution, heuristics, and the LLM
rescue path all fail.
"""

import pytest

from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor

MAX_STEPS = 10


@pytest.mark.asyncio
async def test_circuit_breaker_halts_infinite_loops(monkeypatch):
    """Fitness: the real graph reaches HITL within a bounded number of steps."""

    invalid_api_key = "INVALID_KEY_FITNESS_TEST"
    monkeypatch.setenv("GOOGLE_API_KEY", invalid_api_key)

    initial_state = {
        "instruction": "easy_apply",
        "portal_name": "fitness_test",
        "job_id": "fitness-depth-test",
        "portal_mode": "fitness_test",
        "current_url": "https://example.com",
        "current_state_id": "start",
        "dom_elements": [],
        "screenshot_b64": None,
        "profile_data": {},
        "job_data": {},
        "session_memory": {},
        "errors": [],
        "history": [],
        "patched_components": {},
        "path_id": None,
        "current_mission_id": "test",
    }

    step_count = 0
    final_node = None
    visited_nodes = []
    llm_rescue_update = None

    config = {
        "configurable": {
            "thread_id": "fitness-depth-test",
            "motor_name": "crawl4ai",
            "record_graph": False,
        }
    }

    executor = Crawl4AIExecutor()
    async with executor as active_executor:
        config["configurable"]["executor"] = active_executor
        async with create_ariadne_graph(use_memory=False) as app:
            async for chunk in app.astream(
                initial_state,
                config,
                stream_mode="updates",
            ):
                step_count += 1
                final_node = list(chunk.keys())[-1]
                visited_nodes.append(final_node)
                if "llm_rescue_agent" in chunk:
                    llm_rescue_update = chunk["llm_rescue_agent"]
                assert step_count <= MAX_STEPS, (
                    f"Circuit breaker failed: graph exceeded {MAX_STEPS} steps "
                    f"without reaching HITL. Last node: {final_node}"
                )

    assert visited_nodes[:4] == [
        "observe",
        "execute_deterministic",
        "apply_local_heuristics",
        "llm_rescue_agent",
    ]
    assert final_node == "__interrupt__", (
        f"Graph did not route into HITL interrupt. Final node: {final_node}"
    )
    assert llm_rescue_update is not None
    assert llm_rescue_update["errors"]
    assert llm_rescue_update["errors"][0].startswith("AgentRescueError:")
    assert llm_rescue_update["session_memory"]["agent_failures"] >= 1
