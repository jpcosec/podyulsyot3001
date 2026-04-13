---
type: pattern
domain: architecture
source: tests/architecture/test_graph_depth.py
---

# Pill: Failing Executor Pattern (Mocking)

## Pattern
When testing failure cascades or circuit breakers, use a `FailingExecutor` that simulates errors without needing a real browser or network.

## Implementation
```python
class FailingExecutor:
    """Mock executor that simulates errors for testing cascade failure."""
    def __init__(self):
        self.call_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def take_snapshot(self):
        # Result required for observe_node to continue
        from src.automation.ariadne.contracts.base import SnapshotResult
        return SnapshotResult(url="https://err.com", dom_elements=[], screenshot_b64="fake")

    async def execute(self, command):
        # Result required for execute_deterministic to fail
        from src.automation.ariadne.contracts.base import ExecutionResult
        self.call_count += 1
        return ExecutionResult(status="failed", error="Intentional Failure")
```

## When to use
Use in Phase 0/2 integration tests (`test_graph_depth.py`, "Corneta Test").

## Verify
Verify that `executor.call_count` increments correctly when the graph attempts to execute actions.
