"""Unit tests for Ariadne 2.0 Observe Node."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.automation.ariadne.graph.orchestrator import observe_node
from src.automation.ariadne.contracts.base import SnapshotResult
from src.automation.ariadne.models import (
    AriadneObserve,
    AriadneState,
    AriadneStateDefinition,
)


@pytest.mark.asyncio
async def test_observe_node_success():
    """Verify that observe_node fetches snapshot and updates state."""
    # 1. Setup Mock Executor
    mock_executor = AsyncMock()
    mock_snapshot = SnapshotResult(
        url="https://real-site.com",
        dom_elements=[{"tag": "button", "text": "Apply"}],
        screenshot_b64="base64-data",
    )
    mock_executor.take_snapshot.return_value = mock_snapshot

    # 2. Setup State and Config
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
        "portal_mode": "default",
    }

    config = {"configurable": {"executor": mock_executor}}

    mock_mode = MagicMock()
    mock_mode.inspect_danger.return_value = MagicMock(findings=[])
    mock_map = MagicMock()
    mock_map.states = {
        "start": AriadneStateDefinition(
            id="start",
            description="start",
            presence_predicate=AriadneObserve(required_elements=[]),
        )
    }
    mock_map.success_states = []

    with (
        patch(
            "src.automation.ariadne.graph.orchestrator.MapRepository"
        ) as mock_repo_class,
        patch(
            "src.automation.ariadne.graph.orchestrator.ModeRegistry.get_mode_for_url",
            return_value=mock_mode,
        ),
    ):
        mock_repo_class.return_value.get_map.return_value = mock_map

        # 3. Run Node
        result = await observe_node(state, config)

    # 4. Verify
    assert result["current_url"] == "https://real-site.com"
    assert result["dom_elements"] == [{"tag": "button", "text": "Apply"}]
    assert result["screenshot_b64"] == "base64-data"
    mock_executor.take_snapshot.assert_called_once()


@pytest.mark.asyncio
async def test_observe_node_missing_executor():
    """Verify that observe_node returns an error if executor is missing."""
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
        "portal_mode": "default",
    }

    config = {"configurable": {}}  # No executor

    result = await observe_node(state, config)

    assert "errors" in result
    assert "ExecutorNotFoundError" in result["errors"][0]


@pytest.mark.asyncio
async def test_observe_node_executor_error():
    """Verify that observe_node returns an error if take_snapshot fails."""
    mock_executor = AsyncMock()
    mock_executor.take_snapshot.side_effect = Exception("Browser crashed")

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
        "portal_mode": "default",
    }

    config = {"configurable": {"executor": mock_executor}}

    result = await observe_node(state, config)

    assert "errors" in result
    assert "ObservationError" in result["errors"][0]
    assert "Browser crashed" in result["errors"][0]
