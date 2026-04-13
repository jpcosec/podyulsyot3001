import pytest
from unittest.mock import patch

from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor


@pytest.mark.asyncio
async def test_executor_maintains_single_browser_session():
    """Fitness: browser opens once and closes once across a graph run."""
    enter_count = 0
    exit_count = 0

    original_aenter = Crawl4AIExecutor.__aenter__
    original_aexit = Crawl4AIExecutor.__aexit__

    async def tracked_aenter(self):
        nonlocal enter_count
        enter_count += 1
        return await original_aenter(self)

    async def tracked_aexit(self, *args):
        nonlocal exit_count
        exit_count += 1
        return await original_aexit(self, *args)

    initial_state = {
        "job_id": "fitness-browser-test",
        "portal_name": "fitness_test",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_mission_id": "test",
        "current_state_id": "start",
        "dom_elements": [],
        "current_url": "raw:<html><body><main>fitness test</main></body></html>",
        "screenshot_b64": None,
        "session_memory": {"agent_failures": 2},
        "errors": [],
        "history": [],
        "portal_mode": "fitness_test",
        "patched_components": {},
    }

    with patch.object(Crawl4AIExecutor, "__aenter__", tracked_aenter):
        with patch.object(Crawl4AIExecutor, "__aexit__", tracked_aexit):
            executor = Crawl4AIExecutor()
            executor.current_url = initial_state["current_url"]
            config = {
                "configurable": {
                    "thread_id": "fitness-browser-test",
                    "motor_name": "crawl4ai",
                    "record_graph": False,
                }
            }

            async with executor as active_executor:
                config["configurable"]["executor"] = active_executor

                async with create_ariadne_graph(use_memory=False) as app:
                    events = []
                    async for chunk in app.astream(initial_state, config):
                        events.append(chunk)

                    snapshot = await app.aget_state(config)

    node_names = [
        list(event.keys())[0] for event in events if "__interrupt__" not in event
    ]

    assert node_names == [
        "observe",
        "execute_deterministic",
        "apply_local_heuristics",
        "llm_rescue_agent",
    ]
    assert "__interrupt__" in events[-1]
    assert "human_in_the_loop" in snapshot.next
    assert enter_count == 1, f"Browser opened {enter_count} times - singleton violated"
    assert exit_count == 1, f"Browser closed {exit_count} times - singleton violated"
