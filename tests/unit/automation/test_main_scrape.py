"""Tests for discovery CLI wiring."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.automation.ariadne.models import (
    AriadneMap,
    AriadneMapMeta,
    AriadneObserve,
    AriadneStateDefinition,
)
from src.automation.main import run_scrape


@pytest.mark.asyncio
async def test_run_scrape_uses_search_map_and_discovery_mission(capsys):
    """Scrape should initialize the discovery mission and print extracted memory."""
    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(source="linkedin", flow="search"),
        states={
            "search_results": AriadneStateDefinition(
                id="search_results",
                description="results",
                presence_predicate=AriadneObserve(required_elements=[]),
            ),
            "discovery_complete": AriadneStateDefinition(
                id="discovery_complete",
                description="done",
                presence_predicate=AriadneObserve(required_elements=[]),
            ),
        },
        edges=[],
        success_states=["discovery_complete"],
        failure_states=[],
    )

    fake_app = MagicMock()

    async def fake_astream(initial_state, config, stream_mode="updates"):
        assert initial_state["current_mission_id"] == "discovery"
        assert initial_state["portal_mode"] == "search"
        assert initial_state["job_data"]["limit"] == 3
        yield {
            "execute_deterministic": {
                "current_state_id": "discovery_complete",
                "session_memory": {"limit": 3, "jobs_text": "Job A"},
            }
        }

    fake_app.astream = fake_astream
    fake_app.aget_state = AsyncMock(
        return_value=SimpleNamespace(
            values={
                "current_state_id": "discovery_complete",
                "session_memory": {"limit": 3, "jobs_text": "Job A"},
            }
        )
    )

    @asynccontextmanager
    async def fake_graph_context(*args, **kwargs):
        yield fake_app

    with (
        patch("src.automation.main.MapRepository") as mock_repo_class,
        patch(
            "src.automation.main.MotorRegistry.get_executor", return_value=MagicMock()
        ),
        patch("src.automation.main.create_ariadne_graph", fake_graph_context),
    ):
        mock_repo_class.return_value.get_map.return_value = ariadne_map
        await run_scrape(source="linkedin", limit=3)

    output = capsys.readouterr().out
    assert "Discovery Success" in output
    assert '"jobs_text": "Job A"' in output
