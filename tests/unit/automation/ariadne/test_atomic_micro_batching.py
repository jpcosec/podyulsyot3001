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
from src.automation.ariadne.translators.crawl4ai import Crawl4AITranslator
from src.automation.ariadne.graph.orchestrator import execute_deterministic_node, _find_safe_sequence
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
            {"selector": "#submit-btn"}
        ],
        "current_url": "https://example.com/form",
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "easy_apply"
    }

@pytest.fixture
def mock_map_repo(monkeypatch):
    """Fixture to mock the MapRepository."""
    mock_repo = MagicMock(spec=MapRepository)
    
    # Define a simple map with 3 edges from the same state
    # This simulates a form-filling scenario perfect for batching
    ariadne_map = AriadneMap(
        meta=AriadneMapMeta(portal_name="test-portal", version="1.0"),
        states={
            "state1": AriadneStateDefinition(
                components={
                    "input1": AriadneTarget(css="#input1"),
                    "input2": AriadneTarget(css="#input2"),
                    "submit": AriadneTarget(css="#submit-btn"),
                },
                presence_predicate=AriadneObserve(url_contains="form"),
            ),
            "state2": AriadneStateDefinition(
                presence_predicate=AriadneObserve(url_contains="success"),
            )
        },
        edges=[
            AriadneEdge(from_state="state1", to_state="state1", target="input1", intent=AriadneIntent.FILL, value="val1"),
            AriadneEdge(from_state="state1", to_state="state1", target="input2", intent=AriadneIntent.FILL, value="val2"),
            AriadneEdge(from_state="state1", to_state="state2", target="submit", intent=AriadneIntent.CLICK),
        ]
    )
    
    mock_repo.get_map.return_value = ariadne_map
    
    monkeypatch.setattr('src.automation.ariadne.graph.orchestrator.MapRepository', lambda: mock_repo)
    return mock_repo


@pytest.mark.asyncio
async def test_atomic_fallback_on_batch_failure(mock_state, mock_map_repo):
    """
    Verify that if a batch execution fails at a specific index, the orchestrator
    retries the remaining actions atomically.
    """
    # 1. Setup Mock Executor
    mock_executor = AsyncMock()
    
    # Simulate a 3-action batch. First execution fails at index 1.
    # The subsequent atomic executions for action 2 should succeed.
    mock_executor.execute.side_effect = [
        # First call (the batch) -> fails at index 1
        ExecutionResult(status="failed", failed_at_index=1, error="Element #input2 not found"),
        # Second call (atomic retry of the 3rd action) -> succeeds
        ExecutionResult(status="success"),
    ]

    # 2. Setup Config
    config = {
        "configurable": {
            "executor": mock_executor,
            "motor_name": "crawl4ai"
        }
    }

    # 3. Run the node
    result = await execute_deterministic_node(mock_state, config)

    # 4. Assertions
    assert not result.get("errors"), "Node should not report an error if atomic retry succeeds"
    assert result["current_state_id"] == "state2", "Should end in the final state of the sequence"
    
    # Verify the executor was called correctly
    assert mock_executor.execute.call_count == 2
    
    # First call should be the big batch script
    first_call_cmd = mock_executor.execute.call_args_list[0].args[0]
    assert isinstance(first_call_cmd, CrawlCommand)
    # Check that it's a batch script with our try/catch logic
    assert "try {" in first_call_cmd.c4a_script
    assert "return { 'failed_at': 0, 'error': e.message }" in first_call_cmd.c4a_script
    assert 'await page.fill("#input2", "val2")' in first_call_cmd.c4a_script
    assert 'await page.click("#submit-btn")' in first_call_cmd.c4a_script

    # Second call should be the atomic retry of the last action
    second_call_cmd = mock_executor.execute.call_args_list[1].args[0]
    assert isinstance(second_call_cmd, CrawlCommand)
    assert 'await page.click("#submit-btn")' in second_call_cmd.c4a_script
    # Ensure it's a simple script, not a batch
    assert "try {" not in second_call_cmd.c4a_script
    assert "failed_at" not in second_call_cmd.c4a_script
    
    print("Test passed: Orchestrator correctly fell back to atomic execution.")

@pytest.mark.asyncio
async def test_full_batch_failure_stops_execution(mock_state, mock_map_repo):
    """
    Verify that if the atomic retry fails, the whole execution is marked as failed.
    """
    # 1. Setup Mock Executor
    mock_executor = AsyncMock()
    
    # Simulate failure at index 1 for the batch, and then failure on the atomic retry
    mock_executor.execute.side_effect = [
        ExecutionResult(status="failed", failed_at_index=1, error="Element #input2 not found"),
        ExecutionResult(status="failed", error="Could not click submit button"),
    ]

    # 2. Setup Config
    config = {"configurable": {"executor": mock_executor}}

    # 3. Run the node
    result = await execute_deterministic_node(mock_state, config)

    # 4. Assertions
    assert result.get("errors") is not None, "Node should report an error"
    assert "Atomic retry failed" in result["errors"][0]
    
    assert mock_executor.execute.call_count == 2
    print("Test passed: Orchestrator correctly reported failure after atomic retry failed.")

def test_crawl4ai_translator_generates_correct_atomic_batch_script(mock_state):
    """
    Verify the translator creates a JS script with the correct try/catch structure.
    """
    translator = Crawl4AITranslator()
    
    batch = [
        (AriadneIntent.FILL, AriadneTarget(css="#name"), "John Doe"),
        (AriadneIntent.CLICK, AriadneTarget(css="#submit"), None),
    ]
    
    cmd = translator.translate_batch(batch, mock_state)
    
    assert isinstance(cmd, CrawlCommand)
    
    expected_script = """try {
  // Action 0
  try {
    await page.fill("#name", "John Doe");
  } catch (e) {
    return { 'failed_at': 0, 'error': e.message };
  }
  // Action 1
  try {
    await page.click("#submit");
  } catch (e) {
    return { 'failed_at': 1, 'error': e.message };
  }
} catch (e) {
  return { 'failed_at': -1, 'error': `Unexpected batch error: ${e.message}` };
}"""
    
    assert cmd.c4a_script == expected_script
    print("Test passed: Translator generates correct atomic batch script.")

# To run this test:
# pytest tests/unit/automation/ariadne/test_atomic_micro_batching.py
