# Fitness Function 2: Single Browser Lifecycle
# Protege la persistencia de sesión - navegador debe abrirse una vez

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.automation.ariadne.graph.orchestrator import create_ariadne_graph


@pytest.mark.asyncio
async def test_browser_opens_once_per_session():
    """Fitness: Browser opens exactly once, closes exactly once per graph session."""
    enter_count = 0
    exit_count = 0

    class TrackedCrawler:
        def __init__(self):
            self.url = "https://example.com"

        async def __aenter__(self):
            nonlocal enter_count
            enter_count += 1
            return self

        async def __aexit__(self, *args):
            nonlocal exit_count
            exit_count += 1

        async def arun(self, url, config=None):
            result = MagicMock()
            result.success = True
            result.url = url
            result.screenshot = "fake_b64"
            result.js_script_result = None
            return result

    class TrackedExecutor:
        def __init__(self):
            self._crawler = TrackedCrawler()
            self._session_id = "test"

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
            from src.automation.ariadne.contracts.base import ExecutionResult

            return ExecutionResult(status="success")

    executor = TrackedExecutor()
    initial_state = {
        "job_id": "fitness_test_2",
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
            "thread_id": "fitness_test_2",
            "executor": executor,
            "motor_name": "crawl4ai",
            "record_graph": False,
        }
    }

    async with create_ariadne_graph(use_memory=True) as app:
        await app.ainvoke(initial_state, config)

    assert enter_count == 1, f"Browser opened {enter_count} times, expected 1"
    assert exit_count == 1, f"Browser closed {exit_count} times, expected 1"
