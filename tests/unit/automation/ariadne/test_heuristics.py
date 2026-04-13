"""Tests for Ariadne Local Heuristics logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.automation.ariadne.graph.orchestrator import (
    apply_local_heuristics_node,
    route_after_heuristics,
    MAX_HEURISTIC_RETRIES,
)
from src.automation.ariadne.models import (
    AriadneTarget,
    AriadneStateDefinition,
    AriadneMap,
    AriadneMapMeta,
    AriadneObserve,
)
from src.automation.ariadne.repository import MapRepository


@pytest.mark.asyncio
async def test_apply_local_heuristics_node_success():
    """Verify that apply_local_heuristics_node correctly patches components and clears errors."""
    mock_mode = MagicMock()
    mock_mode.apply_local_heuristics = AsyncMock()

    original_target = AriadneTarget(css="#old")
    definition = AriadneStateDefinition(
        id="state1",
        description="test",
        presence_predicate=AriadneObserve(required_elements=[]),
        components={"btn": original_target},
    )

    patched_target = AriadneTarget(css="#new")
    patched_definition = AriadneStateDefinition(
        id="state1",
        description="test",
        presence_predicate=AriadneObserve(required_elements=[]),
        components={"btn": patched_target},
    )
    mock_mode.apply_local_heuristics.return_value = patched_definition

    mock_map = AriadneMap(
        meta=AriadneMapMeta(source="test", flow="test"),
        states={"state1": definition},
        edges=[],
        success_states=[],
        failure_states=[],
    )

    mock_repo_instance = MagicMock()
    mock_repo_instance.get_map_async = AsyncMock(return_value=mock_map)

    with (
        patch(
            "src.automation.ariadne.modes.registry.ModeRegistry.get_mode_for_url",
            return_value=mock_mode,
        ),
        patch(
            "src.automation.ariadne.graph.orchestrator.MapRepository",
            return_value=mock_repo_instance,
        ),
    ):
        state = {
            "portal_name": "test-portal",
            "current_state_id": "state1",
            "portal_mode": "test-mode",
            "errors": ["SomeError"],
            "patched_components": {},
            "session_memory": {},
        }

        config = {"configurable": {}}

        result = await apply_local_heuristics_node(state, config)

        assert result["errors"] == []
        assert "state1:btn" in result["patched_components"]
        assert result["patched_components"]["state1:btn"].css == "#new"
        assert result["session_memory"]["heuristic_retries"] == 1


@pytest.mark.asyncio
async def test_apply_local_heuristics_node_no_patch():
    """Verify that apply_local_heuristics_node returns empty dict when no patches are found."""
    mock_mode = MagicMock()
    mock_mode.apply_local_heuristics = AsyncMock()

    definition = AriadneStateDefinition(
        id="state1",
        description="test",
        presence_predicate=AriadneObserve(required_elements=[]),
        components={"btn": AriadneTarget(css="#old")},
    )

    mock_mode.apply_local_heuristics.return_value = definition

    mock_map = AriadneMap(
        meta=AriadneMapMeta(source="test", flow="test"),
        states={"state1": definition},
        edges=[],
        success_states=[],
        failure_states=[],
    )

    mock_repo_instance = MagicMock()
    mock_repo_instance.get_map_async = AsyncMock(return_value=mock_map)

    with (
        patch(
            "src.automation.ariadne.modes.registry.ModeRegistry.get_mode_for_url",
            return_value=mock_mode,
        ),
        patch(
            "src.automation.ariadne.graph.orchestrator.MapRepository",
            return_value=mock_repo_instance,
        ),
    ):
        state = {
            "portal_name": "test-portal",
            "current_state_id": "state1",
            "portal_mode": "test-mode",
            "errors": ["SomeError"],
            "session_memory": {},
        }

        result = await apply_local_heuristics_node(state, {})

        assert result == {}


def test_route_after_heuristics_uses_circuit_breaker():
    """Heuristics retries should eventually escalate to the LLM rescue agent."""
    assert (
        route_after_heuristics({"errors": ["boom"], "session_memory": {}})
        == "llm_rescue_agent"
    )
    assert (
        route_after_heuristics(
            {
                "errors": [],
                "session_memory": {"heuristic_retries": MAX_HEURISTIC_RETRIES},
            }
        )
        == "llm_rescue_agent"
    )
    assert (
        route_after_heuristics(
            {"errors": [], "session_memory": {"heuristic_retries": 1}}
        )
        == "execute_deterministic"
    )
