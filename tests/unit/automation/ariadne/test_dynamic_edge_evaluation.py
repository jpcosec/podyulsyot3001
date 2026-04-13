"""Unit tests for the Deterministic Dispatch Node."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.automation.ariadne.contracts.base import (
    AriadneIntent,
    AriadneTarget,
    ExecutionResult,
)
from src.automation.ariadne.models import (
    AriadneEdge,
    AriadneMap,
    AriadneMapMeta,
    AriadneState,
    AriadneStateDefinition,
    AriadneObserve,
)
from src.automation.ariadne.graph.orchestrator import execute_deterministic_node


@pytest.mark.asyncio
async def test_dynamic_edge_evaluation():
    """Verify that the node picks the edge whose target exists on the page."""
    # State with 2 possible buttons, but only "apply_b" is in the snapshot
    mock_state: AriadneState = {
        "portal_name": "test_portal",
        "current_state_id": "details",
        "dom_elements": [{"selector": "#apply_b", "text": "Apply Now"}],
        # other fields omitted for brevity
    }

    mock_map = AriadneMap(
        meta=AriadneMapMeta(source="test_portal", flow="test"),
        states={
            "details": AriadneStateDefinition(
                id="details",
                description="test",
                presence_predicate=AriadneObserve(),
                components={
                    "apply_a": AriadneTarget(css="#apply_a"),
                    "apply_b": AriadneTarget(css="#apply_b"),
                },
            )
        },
        edges=[
            AriadneEdge(
                from_state="details",
                to_state="form",
                intent=AriadneIntent.CLICK,
                target="apply_a",
            ),
            AriadneEdge(
                from_state="details",
                to_state="form",
                intent=AriadneIntent.CLICK,
                target="apply_b",
            ),
        ],
        success_states=[],
        failure_states=[],
    )

    # Mock the repository
    with patch(
        "src.automation.ariadne.repository.MapRepository.get_map_async",
        new_callable=AsyncMock,
        return_value=mock_map,
    ):
        mock_executor = AsyncMock()
        mock_executor.execute.return_value = ExecutionResult(status="success")

        config = {
            "configurable": {"executor": mock_executor, "motor_name": "browseros"}
        }

        # Run the node
        result_state = await execute_deterministic_node(mock_state, config)

        # Verify the correct edge was chosen
        assert not result_state.get("errors")

        # Get the command that was sent to the executor
        executed_command = mock_executor.execute.call_args[0][0]

        # The selector_text should be from apply_b, not apply_a
        assert executed_command.selector_text == "#apply_b"
