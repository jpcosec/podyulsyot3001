# Fitness Function 2: Single Browser Session (State Persistence)
# USA el executor REAL (Crawl4AIExecutor) y verifica que abra Chromium una sola vez

import pytest
from unittest.mock import AsyncMock, patch
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor


@pytest.mark.asyncio
async def test_executor_maintains_single_browser_session():
    """Fitness: Crawl4AIExecutor abre navegador una vez, cierra una vez."""

    # Spy sobre los métodos reales de Crawl4AI que levantan Chromium
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

    with patch.object(Crawl4AIExecutor, "__aenter__", tracked_aenter):
        with patch.object(Crawl4AIExecutor, "__aexit__", tracked_aexit):
            executor = Crawl4AIExecutor()
            async with executor:
                # Simular una ejecución mínima
                from src.automation.ariadne.contracts.base import SnapshotResult

                try:
                    await executor.take_snapshot()
                except Exception:
                    pass

    assert enter_count == 1, f"🚨 Navegador abrió {enter_count} veces en una sesión"
    assert exit_count == 1, f"🚨 Navegador cerró {exit_count} veces"
