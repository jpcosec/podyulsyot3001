"""Tests for Deterministic Dispatch Logic in Ariadne 2.0 Orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.automation.ariadne.graph.orchestrator import execute_deterministic_node
from src.automation.ariadne.contracts.base import ExecutionResult, MotorCommand
from src.automation.ariadne.models import AriadneState, AriadneMap, AriadneEdge, AriadneIntent, AriadneTarget


@pytest.mark.asyncio
async def test_execute_deterministic_node_success():
    """Verify that execute_deterministic_node calls the executor and updates state."""
    
    # 1. Mock Map and Repository
    mock_edge = AriadneEdge(
        from_state="start",
        to_state="next_state",
        intent=AriadneIntent.CLICK,
        target=AriadneTarget(css="#apply-button")
    )
    mock_map = MagicMock(spec=AriadneMap)
    mock_map.edges = [mock_edge]
    mock_map.states = {"start": MagicMock(), "next_state": MagicMock()}

    with patch("src.automation.ariadne.graph.orchestrator.MapRepository") as mock_repo_class:
        mock_repo = mock_repo_class.return_value
        mock_repo.get_map.return_value = mock_map

        # 2. Mock Executor
        mock_executor = AsyncMock()
        mock_executor.execute.return_value = ExecutionResult(status="success")

        # 3. Setup State and Config
        state: AriadneState = {
            "job_id": "test-job",
            "portal_name": "test-portal",
            "profile_data": {},
            "job_data": {},
            "path_id": None,
            "current_state_id": "start",
            "dom_elements": [],
            "current_url": "",
            "screenshot_b64": None,
            "session_memory": {},
            "errors": [],
            "history": [],
            "portal_mode": "default"
        }
        
        # We'll try to provide the executor in config
        config = {"configurable": {"executor": mock_executor}}

        # 4. Run Node
        result = await execute_deterministic_node(state, config)

        # 5. Verify
        assert result["current_state_id"] == "next_state"
        assert result["errors"] == []
        
        # Check if executor was called
        # Currently, it shouldn't be called because the TODO is not implemented.
        # Once implemented, we want this to be true.
        assert mock_executor.execute.called
