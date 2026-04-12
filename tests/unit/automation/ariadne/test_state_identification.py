"""Unit tests for State Identification and Danger Detection in Observe Node."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.automation.ariadne.graph.orchestrator import observe_node
from src.automation.ariadne.contracts.base import SnapshotResult, AriadneTarget
from src.automation.ariadne.models import (
    AriadneState,
    AriadneMap,
    AriadneStateDefinition,
    AriadneObserve,
    AriadneMapMeta,
)
from src.automation.ariadne.danger_contracts import (
    ApplyDangerReport,
    ApplyDangerFinding,
)


@pytest.mark.asyncio
async def test_observe_node_identifies_state():
    """Verify that observe_node identifies the current state from the map."""
    # 1. Setup Mock Executor and Snapshot
    mock_executor = AsyncMock()
    mock_snapshot = SnapshotResult(
        url="https://linkedin.com/jobs/view/123",
        dom_elements=[
            {"tag": "button", "text": "Easy Apply", "css": "button.jobs-apply-button"},
            {"tag": "div", "text": "Job description", "css": ".jobs-description"},
        ],
        screenshot_b64="base64-data",
    )
    mock_executor.take_snapshot.return_value = mock_snapshot

    # 2. Setup Mock Map
    mock_map = AriadneMap(
        meta=AriadneMapMeta(source="linkedin", flow="easy_apply"),
        states={
            "job_details": AriadneStateDefinition(
                id="job_details",
                description="Job details page",
                presence_predicate=AriadneObserve(
                    required_elements=[
                        AriadneTarget(css=".jobs-description", text="Job description")
                    ]
                ),
                components={},
            )
        },
        edges=[],
        success_states=["apply_success"],
        failure_states=[],
    )

    # 3. Setup State and Config
    state: AriadneState = {
        "job_id": "test-job",
        "portal_name": "linkedin",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_state_id": "unknown",
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "default",
        "patched_components": {},
    }

    config = {"configurable": {"executor": mock_executor}}

    # 4. Run Node with Mocks
    with patch(
        "src.automation.ariadne.repository.MapRepository.get_map", return_value=mock_map
    ):
        result = await observe_node(state, config)

    # 5. Verify
    print(f"DEBUG: result keys: {result.keys()}")
    assert result["current_state_id"] == "job_details"
    assert result["current_url"] == "https://linkedin.com/jobs/view/123"
    assert (
        "session_memory" not in result
        or "danger_detected" not in result["session_memory"]
    )


@pytest.mark.asyncio
async def test_observe_node_detects_danger():
    """Verify that observe_node detects danger via portal mode."""
    # 1. Setup Mock Executor and Snapshot
    mock_executor = AsyncMock()
    mock_snapshot = SnapshotResult(
        url="https://linkedin.com/captcha",
        dom_elements=[{"text": "Please solve this CAPTCHA"}],
        screenshot_b64="base64-data",
    )
    mock_executor.take_snapshot.return_value = mock_snapshot

    # 2. Setup Mock Danger Report
    mock_danger_report = ApplyDangerReport(
        findings=[
            ApplyDangerFinding(
                code="CAPTCHA_DETECTED",
                source="dom_text",
                recommended_action="pause",
                message="A CAPTCHA was found on the page.",
            )
        ]
    )

    # 3. Setup State
    state: AriadneState = {
        "job_id": "test-job",
        "portal_name": "linkedin",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_state_id": "unknown",
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "default",
        "patched_components": {},
    }

    config = {"configurable": {"executor": mock_executor}}

    # 4. Run Node with Mocks
    with patch(
        "src.automation.ariadne.repository.MapRepository.get_map",
        side_effect=Exception("No map"),
    ):
        with patch(
            "src.automation.ariadne.modes.registry.ModeRegistry.get_mode_for_url"
        ) as mock_get_mode:
            mock_mode = MagicMock()
            mock_mode.inspect_danger = AsyncMock(return_value=mock_danger_report)
            mock_get_mode.return_value = mock_mode

            result = await observe_node(state, config)

    # 5. Verify
    assert result["session_memory"]["danger_detected"] is True
    assert result["session_memory"]["danger_findings"][0]["code"] == "CAPTCHA_DETECTED"


@pytest.mark.asyncio
async def test_observe_node_goal_achieved():
    """Verify that observe_node detects goal achievement when reaching a success state."""
    # 1. Setup Mock Executor and Snapshot
    mock_executor = AsyncMock()
    mock_snapshot = SnapshotResult(
        url="https://linkedin.com/success",
        dom_elements=[{"text": "Application sent"}],
        screenshot_b64="base64-data",
    )
    mock_executor.take_snapshot.return_value = mock_snapshot

    # 2. Setup Mock Map with Success State
    mock_map = AriadneMap(
        meta=AriadneMapMeta(source="linkedin", flow="easy_apply"),
        states={
            "apply_success": AriadneStateDefinition(
                id="apply_success",
                description="Success page",
                presence_predicate=AriadneObserve(
                    required_elements=[AriadneTarget(text="Application sent")]
                ),
                components={},
            )
        },
        edges=[],
        success_states=["apply_success"],
        failure_states=[],
    )

    # 3. Setup State
    state: AriadneState = {
        "job_id": "test-job",
        "portal_name": "linkedin",
        "profile_data": {},
        "job_data": {},
        "path_id": None,
        "current_state_id": "unknown",
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "default",
        "patched_components": {},
    }

    config = {"configurable": {"executor": mock_executor}}

    # 4. Run Node
    with patch(
        "src.automation.ariadne.repository.MapRepository.get_map", return_value=mock_map
    ):
        result = await observe_node(state, config)

    # 5. Verify
    assert result["current_state_id"] == "apply_success"
    assert result["session_memory"]["goal_achieved"] is True
