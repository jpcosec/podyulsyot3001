# Fitness Function 1: Synchronous I/O in Hot Loop
# SOLO detecta I/O síncrono durante la ejecución del grafo (NO en boot/caching)

import builtins
from unittest.mock import patch

import pytest

from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.ariadne.repository import MapRepository
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor


class SyncIODetector:
    """Detecta I/O síncrono SOLO durante ejecución del grafo."""

    def __init__(self):
        self.hot_loop_calls = []
        self.boot_complete = False

    def start(self):
        self.boot_complete = False
        original_open = builtins.open

        def tracked_open(*args, **kwargs):
            filename = str(args[0]) if args else ""

            # Solo capturamos si es un mapa JSON Y la fase de boot terminó
            if (
                self.boot_complete
                and "portals/" in filename
                and filename.endswith(".json")
            ):
                import traceback

                self.hot_loop_calls.append(
                    {"file": filename, "stack": traceback.format_stack()[-3:-1]}
                )

            return original_open(*args, **kwargs)

        self._patcher = patch("builtins.open", tracked_open)
        self._patcher.start()

        # Boot完了 - a partir de aquí todo es hot-loop
        self.boot_complete = True

    def stop(self):
        if self._patcher:
            self._patcher.stop()


@pytest.mark.asyncio
async def test_no_sync_io_in_hot_loop():
    """Fitness: no synchronous disk I/O during graph node execution."""

    MapRepository()

    detector = SyncIODetector()
    detector.start()

    initial_state = {
        "instruction": "easy_apply",
        "portal_name": "fitness_test",
        "job_id": "fitness-sync-io-test",
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
        "current_mission_id": "easy_apply",
    }

    config = {
        "configurable": {
            "thread_id": "fitness-sync-io-test",
            "motor_name": "crawl4ai",
            "record_graph": False,
        }
    }

    try:
        executor = Crawl4AIExecutor()
        async with executor as active_executor:
            config["configurable"]["executor"] = active_executor
            async with create_ariadne_graph(use_memory=False) as app:
                async for _ in app.astream(initial_state, config):
                    pass

            if detector.hot_loop_calls:
                files = [call["file"] for call in detector.hot_loop_calls[:3]]
                pytest.fail(
                    f"Sync I/O detected in hot loop: {len(detector.hot_loop_calls)} reads. "
                    f"Files: {files}"
                )
    finally:
        detector.stop()
