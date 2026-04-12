"""Tests for the JIT Micro-Batching Optimizer."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.automation.ariadne.models import (
    AriadneIntent,
    AriadneState,
    AriadneTarget,
    AriadneEdge,
    AriadneMap,
    AriadneStateDefinition,
    AriadneObserve,
    AriadneMapMeta,
    CrawlCommand,
    ExecutionResult
)
from src.automation.ariadne.translators.crawl4ai import Crawl4AITranslator
from src.automation.ariadne.graph.orchestrator import execute_deterministic_node


@pytest.fixture
def mock_state() -> AriadneState:
    return {
        "job_id": "test-job",
        "portal_name": "test-portal",
        "profile_data": {"name": "John Doe"},
        "job_data": {},
        "path_id": None,
        "current_state_id": "state1",
        "dom_elements": [],
        "current_url": "https://example.com",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "easy_apply"
    }


def test_crawl4ai_translator_batching(mock_state):
    """Verify that Crawl4AITranslator can batch multiple intents into one script."""
    translator = Crawl4AITranslator()
    
    batch = [
        (AriadneIntent.FILL, AriadneTarget(css="#name"), "John Doe"),
        (AriadneIntent.CLICK, AriadneTarget(css="#submit"), None),
    ]
    
    cmd = translator.translate_batch(batch, mock_state)
    
    assert isinstance(cmd, CrawlCommand)
    assert 'await page.fill("#name", "John Doe")' in cmd.c4a_script
    assert 'await page.click("#submit")' in cmd.c4a_script
    assert "\n" in cmd.c4a_script


@pytest.mark.asyncio
async def test_execute_deterministic_batching(mock_state):
    """
    This test will need the orchestrator to be updated to support
    injecting dependencies (MapRepository, Executor, Translator).
    For now, we'll focus on the logic inside the node if we can isolate it.
    """
    # TODO: Once orchestrator.py is updated, add a test here that verifies 
    # that multiple consecutive deterministic edges are batched.
    pass
