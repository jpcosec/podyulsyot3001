"""Unit tests for C4AIMotorProvider / C4AIMotorSession."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider


def test_provider_is_instantiable():
    provider = C4AIMotorProvider()
    assert hasattr(provider, "open_session")


def test_provider_has_no_portal_map():
    provider = C4AIMotorProvider()
    assert not hasattr(provider, "portal_map")
    assert not hasattr(provider, "source_name")


@pytest.mark.asyncio
async def test_open_session_yields_session_with_correct_interface():
    provider = C4AIMotorProvider()
    fake_crawler_ctx = MagicMock()
    fake_crawler_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    fake_crawler_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.automation.motors.crawl4ai.apply_engine.AsyncWebCrawler", return_value=fake_crawler_ctx):
        async with provider.open_session("test-session") as session:
            assert hasattr(session, "observe")
            assert hasattr(session, "execute_step")


@pytest.mark.asyncio
async def test_observe_returns_empty_for_empty_selectors():
    from src.automation.motors.crawl4ai.apply_engine import C4AIMotorSession
    session = C4AIMotorSession(MagicMock(), "sess", MagicMock())
    result = await session.observe(set())
    assert result == {}
