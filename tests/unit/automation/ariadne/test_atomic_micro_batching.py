"""Tests for Atomic Micro-Batching with Failure Indexing."""

import pytest
from unittest.mock import AsyncMock, MagicMock, call

from src.automation.ariadne.contracts.base import (
    AriadneIntent,
    AriadneTarget,
    CrawlCommand,
    ExecutionResult,
)
from src.automation.ariadne.models import (
    AriadneState,
    AriadneEdge,
    AriadneMap,
    AriadneStateDefinition,
    AriadneObserve,
    AriadneMapMeta,
)
from src.automation.adapters.translators.crawl4ai import Crawl4AITranslator
from src.automation.ariadne.graph.orchestrator import (
    execute_deterministic_node,
    _find_safe_sequence,
)
from src.automation.ariadne.repository import MapRepository


@pytest.fixture
def mock_state() -> AriadneState:
    """Fixture for a basic AriadneState."""
    return {
        "job_id": "test-job",
        "portal_name": "test-portal",
        "profile_data": {"name": "John Doe"},
        "job_data": {},
        "path_id": None,
        "current_state_id": "state1",
        "dom_elements": [
            {"selector": "#input1"},
            {"selector": "#input2"},
            {"selector": "#submit-btn"},
        ],
        "current_url": "https://example.com/form",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "easy_apply",
    }


@pytest.fixture
def mock_map_repo(monkeypatch):
    """Fixture to mock the MapRepository."""
    mock_repo = MagicMock(spec=MapRepository)

    # Define a simple map with 3 edges from the same state
    # This simulates a form-filling scenario perfect for batching
    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(source="test-portal", flow="apply", version="1.0"),
        states={
            "state1": AriadneStateDefinition(
                id="state1",
                description="Form state",
                components={
                    "input1": AriadneTarget(css="#input1"),
                    "input2": AriadneTarget(css="#input2"),
                    "submit": AriadneTarget(css="#submit-btn"),
                },
                presence_predicate=AriadneObserve(url_contains="form"),
            ),
            "state2": AriadneStateDefinition(
                id="state2",
                description="Success state",
                presence_predicate=AriadneObserve(url_contains="success"),
            ),
        },
        edges=[
            AriadneEdge(
                from_state="state1",
                to_state="state1",
                target="input1",
                intent=AriadneIntent.FILL,
                value="val1",
            ),
            AriadneEdge(
                from_state="state1",
                to_state="state1",
                target="input2",
                intent=AriadneIntent.FILL,
                value="val2",
            ),
            AriadneEdge(
                from_state="state1",
                to_state="state2",
                target="submit",
                intent=AriadneIntent.CLICK,
            ),
        ],
        success_states=["state2"],
        failure_states=[],
    )

    mock_repo.get_map.return_value = ariadne_map

    monkeypatch.setattr(
        "src.automation.ariadne.graph.orchestrator.MapRepository", lambda: mock_repo
    )
    return mock_repo


@pytest.mark.asyncio
async def test_batch_failure_returns_error(mock_state, mock_map_repo):
    """
    Verify that if a batch execution fails at a specific index, the orchestrator
    returns an error and lets route_after_deterministic handle it (no heroic retry).
    """
    # 1. Setup Mock Executor
    mock_executor = AsyncMock()

    # Simulate a 3-action batch that fails at index 1
    mock_executor.execute.return_value = ExecutionResult(
        status="failed",
        failed_at_index=1,
        completed_count=1,
        error="Element #input2 not found",
    )

    # 2. Setup Config
    config = {"configurable": {"executor": mock_executor, "motor_name": "crawl4ai"}}

    # 3. Run the node
    result = await execute_deterministic_node(mock_state, config)

    # 4. Assertions - batch failure should return error, not retry
    assert result.get("errors"), "Node should report an error when batch fails"
    assert "Batch failed at index" in result["errors"][0]
    assert "ExecutionFailed" in result["errors"][0]

    # Verify executor was called only once (no heroic retry)
    assert mock_executor.execute.call_count == 1
    print("Test passed: Batch failure returns error without heroic retry.")


@pytest.mark.asyncio
async def test_single_action_failure_returns_error(mock_state, mock_map_repo):
    """
    Verify that if a single action execution fails, the orchestrator returns an error.
    """
    # 1. Setup Mock Executor
    mock_executor = AsyncMock()

    # Simulate single action failure
    mock_executor.execute.return_value = ExecutionResult(
        status="failed",
        error="Element #input1 not found",
    )

    # 2. Setup Config - use single action (not batch)
    config = {"configurable": {"executor": mock_executor, "motor_name": "crawl4ai"}}

    # 3. Run the node
    result = await execute_deterministic_node(mock_state, config)

    # 4. Assertions
    assert result.get("errors"), "Node should report an error when single action fails"
    assert "ExecutionFailed" in result["errors"][0]

    # Verify executor was called once
    assert mock_executor.execute.call_count == 1
    print("Test passed: Single action failure returns error.")


def test_crawl4ai_translator_generates_correct_atomic_batch_script(mock_state):
    """
    Verify the translator creates a native C4A-Script batch.
    """
    translator = Crawl4AITranslator()

    batch = [
        (AriadneIntent.FILL, AriadneTarget(css="#name"), "John Doe"),
        (AriadneIntent.CLICK, AriadneTarget(css="#submit"), None),
    ]

    cmd = translator.translate_batch(batch, mock_state)

    assert isinstance(cmd, CrawlCommand)

    expected_script = """# Action 0
SET `#name` "John Doe"
# Action 1
CLICK `#submit`"""

    assert cmd.c4a_script == expected_script
    print("Test passed: Translator generates correct atomic batch script.")


# To run this test:
# pytest tests/unit/automation/ariadne/test_atomic_micro_batching.py
