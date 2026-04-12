# Fitness Function 1: Synchronous I/O Detector
# Protege el Event Loop contra bloqueo síncrono

import pytest
from unittest.mock import patch, MagicMock
from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor


class SyncIODetector:
    """Detects synchronous I/O calls during async execution."""

    def __init__(self):
        self.sync_calls = []
        self._original_open = None

    def start(self):
        self._original_open = open
        original_requests_get = None

        def tracked_open(*args, **kwargs):
            import traceback

            self.sync_calls.append(
                {
                    "func": "open",
                    "args": args[:2],
                    "traceback": traceback.format_stack(),
                }
            )
            return self._original_open(*args, **kwargs)

        self._patcher = patch("builtins.open", tracked_open)
        self._patcher.start()

    def stop(self):
        if self._patcher:
            self._patcher.stop()

    def check(self):
        if self.sync_calls:
            raise RuntimeError(
                f"Synchronous I/O detected during graph execution! "
                f"Calls: {len(self.sync_calls)}. "
                f"First call: {self.sync_calls[0]['args']}"
            )


@pytest.fixture
def sync_io_detector():
    detector = SyncIODetector()
    detector.start()
    yield detector
    detector.stop()


@pytest.mark.asyncio
async def test_no_sync_io_in_hot_loop(sync_io_detector):
    """Fitness: No synchronous I/O in LangGraph hot loop."""
    executor = Crawl4AIExecutor()

    initial_state = {
        "job_id": "fitness_test_1",
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
            "thread_id": "fitness_test_1",
            "executor": executor,
            "motor_name": "crawl4ai",
            "record_graph": False,
        }
    }

    async with executor:
        async with create_ariadne_graph(use_memory=True) as app:
            try:
                await app.ainvoke(initial_state, config)
            except Exception:
                pass

    sync_io_detector.check()
