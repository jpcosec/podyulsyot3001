"""Tests for discovery mission extraction behavior."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.automation.ariadne.contracts.base import (
    AriadneIntent,
    AriadneTarget,
    ExecutionResult,
)
from src.automation.ariadne.graph.orchestrator import execute_deterministic_node
from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneMap,
    AriadneMapMeta,
    AriadneObserve,
    AriadneStateDefinition,
)


@pytest.mark.asyncio
async def test_execute_deterministic_node_captures_discovery_extracts(monkeypatch):
    """Extraction edges should write scraped values into session memory."""
    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(source="linkedin", flow="search"),
        states={
            "search_results": AriadneStateDefinition(
                id="search_results",
                description="results",
                presence_predicate=AriadneObserve(required_elements=[]),
                components={
                    "results_list": AriadneTarget(css=".jobs-search-results-list")
                },
            ),
            "discovery_complete": AriadneStateDefinition(
                id="discovery_complete",
                description="done",
                presence_predicate=AriadneObserve(required_elements=[]),
            ),
        },
        edges=[
            AriadneEdge(
                from_state="search_results",
                to_state="discovery_complete",
                mission_id="discovery",
                intent=AriadneIntent.EXTRACT,
                target="results_list",
                extract={"jobs_text": ".jobs-search-results-list"},
            )
        ],
        success_states=["discovery_complete"],
        failure_states=[],
    )
    monkeypatch.setattr(
        "src.automation.ariadne.graph.orchestrator.MapRepository",
        lambda: MagicMock(get_map=MagicMock(return_value=ariadne_map)),
    )

    executor = AsyncMock()
    executor.execute.return_value = ExecutionResult(status="success")
    state = {
        "portal_name": "linkedin",
        "current_state_id": "search_results",
        "current_mission_id": "discovery",
        "dom_elements": [
            {"selector": ".jobs-search-results-list", "text": "Job A\nJob B"}
        ],
        "session_memory": {},
        "patched_components": {},
        "errors": [],
    }
    config = {"configurable": {"executor": executor, "motor_name": "crawl4ai"}}

    result = await execute_deterministic_node(state, config)

    assert result["current_state_id"] == "discovery_complete"
    assert result["session_memory"]["jobs_text"] == "Job A\nJob B"
