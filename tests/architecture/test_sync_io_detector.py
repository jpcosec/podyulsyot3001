# Fitness Function 1: Synchronous I/O in Hot Loop
# SOLO detecta I/O síncrono durante la ejecución del grafo (NO en boot/caching)

import pytest
import builtins
import asyncio
from unittest.mock import patch
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor
from src.automation.ariadne.repository import MapRepository


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
    """Fitness: No synchronous I/O during graph execution (hot loop only)."""

    # PRE-BOOT: Cargar el repositorio (I/O permitido aquí)
    repo = MapRepository()

    detector = SyncIODetector()
    detector.start()

    try:
        executor = Crawl4AIExecutor()
        async with executor:
            # Simular operaciones reales del grafo
            try:
                await executor.take_snapshot()
            except Exception:
                pass

            # Verificar que no hubo I/O síncrono durante ejecución
            if detector.hot_loop_calls:
                pytest.fail(
                    f"🚨 I/O Síncrono en Hot Loop: {len(detector.hot_loop_calls)} reads. "
                    f"Files: {[c['file'] for c in detector.hot_loop_calls[:3]]}"
                )
    finally:
        detector.stop()
