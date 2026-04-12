"""Tests for Ariadne Local Heuristics logic."""

import pytest
from unittest.mock import MagicMock, patch
from src.automation.ariadne.graph.orchestrator import (
    apply_local_heuristics_node,
    execute_deterministic_node,
)
from src.automation.ariadne.models import (
    AriadneTarget,
    AriadneStateDefinition,
    AriadneMap,
    AriadneMapMeta,
    AriadneObserve,
    AriadneEdge,
    AriadneIntent,
)


@pytest.mark.asyncio
async def test_apply_local_heuristics_node_success():
    """Verify that apply_local_heuristics_node correctly patches components and clears errors."""
    # Mock Mode
    mock_mode = MagicMock()

    # Original definition
    original_target = AriadneTarget(css="#old")
    definition = AriadneStateDefinition(
        id="state1",
        description="test",
        presence_predicate=AriadneObserve(required_elements=[]),
        components={"btn": original_target},
    )

    # Patched definition
    patched_target = AriadneTarget(css="#new")
    patched_definition = AriadneStateDefinition(
        id="state1",
        description="test",
        presence_predicate=AriadneObserve(required_elements=[]),
        components={"btn": patched_target},
    )
    mock_mode.apply_local_heuristics.return_value = patched_definition

    # Mock Map
    mock_map = AriadneMap(
        meta=AriadneMapMeta(source="test", flow="test"),
        states={"state1": definition},
        edges=[],
        success_states=[],
        failure_states=[],
    )

    # Mock Repository and Registry
    with patch(
        "src.automation.ariadne.repository.MapRepository.get_map", return_value=mock_map
    ), patch(
        "src.automation.ariadne.modes.registry.ModeRegistry.get_mode_for_url",
        return_value=mock_mode,
    ):

        state = {
            "portal_name": "test-portal",
            "current_state_id": "state1",
            "portal_mode": "test-mode",
            "errors": ["SomeError"],
            "patched_components": {},
        }

        config = {"configurable": {}}

        result = await apply_local_heuristics_node(state, config)

        assert result["errors"] == []  # Errors cleared
        assert "btn" in result["patched_components"]
        assert result["patched_components"]["btn"].css == "#new"


@pytest.mark.asyncio
async def test_apply_local_heuristics_node_no_patch():
    """Verify that apply_local_heuristics_node returns empty dict when no patches are found."""
    # Mock Mode
    mock_mode = MagicMock()

    definition = AriadneStateDefinition(
        id="state1",
        description="test",
        presence_predicate=AriadneObserve(required_elements=[]),
        components={"btn": AriadneTarget(css="#old")},
    )

    # No changes in patched definition
    mock_mode.apply_local_heuristics.return_value = definition

    mock_map = AriadneMap(
        meta=AriadneMapMeta(source="test", flow="test"),
        states={"state1": definition},
        edges=[],
        success_states=[],
        failure_states=[],
    )

    with patch(
        "src.automation.ariadne.repository.MapRepository.get_map", return_value=mock_map
    ), patch(
        "src.automation.ariadne.modes.registry.ModeRegistry.get_mode_for_url",
        return_value=mock_mode,
    ):

        state = {
            "portal_name": "test-portal",
            "current_state_id": "state1",
            "portal_mode": "test-mode",
            "errors": ["SomeError"],
        }

        result = await apply_local_heuristics_node(state, {})

        assert result == {}  # No changes returned, errors remain


@pytest.mark.asyncio
async def test_execute_deterministic_uses_patches():
    """Verify that execute_deterministic_node uses patched_components from state."""
    # Mock Executor
    mock_executor = MagicMock()

    async def mock_execute(cmd):
        from src.automation.ariadne.contracts.base import ExecutionResult

        return ExecutionResult(status="success")

    mock_executor.execute = mock_execute

    # Mock Map
    # Edge uses a component name "btn"
    edge = AriadneEdge(
        from_state="state1", to_state="state2", intent=AriadneIntent.CLICK, target="btn"
    )

    definition = AriadneStateDefinition(
        id="state1",
        description="test",
        presence_predicate=AriadneObserve(required_elements=[]),
        components={"btn": AriadneTarget(css="#old")},
    )

    mock_map = AriadneMap(
        meta=AriadneMapMeta(source="test", flow="test"),
        states={"state1": definition, "state2": definition},
        edges=[edge],
        success_states=[],
        failure_states=[],
    )

    # Patch for "btn"
    patched_target = AriadneTarget(css="#patched")

    with patch(
        "src.automation.ariadne.repository.MapRepository.get_map", return_value=mock_map
    ):
        state = {
            "portal_name": "test-portal",
            "current_state_id": "state1",
            "patched_components": {"btn": patched_target},
            "errors": [],
        }

        # Mock translator to verify it gets the right target
        with patch(
            "src.automation.ariadne.translators.registry.TranslatorRegistry.get_translator_by_name"
        ) as mock_get_translator:
            mock_translator = MagicMock()
            mock_get_translator.return_value = mock_translator

            config = {
                "configurable": {"executor": mock_executor, "motor_name": "crawl4ai"}
            }

            await execute_deterministic_node(state, config)

            # Check if translate_intent was called with patched_target
            args, _ = mock_translator.translate_intent.call_args
            # args are (intent, target, state, value)
            assert args[1] == patched_target
            assert args[1].css == "#patched"
