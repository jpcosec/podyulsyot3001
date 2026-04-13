---
type: pattern
domain: scraping
source: plan_docs/design/browseros-adapter-lifecycle.md:5
---

# Pill: Peripheral Adapter Pattern

## Pattern
Physical browser adapters own browser I/O and lifecycle. They expose `Sensor` and `Motor` behavior plus health and async context management through one injected object.

## Implementation
```python
class PeripheralAdapter:
    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc, tb): ...
    async def is_healthy(self) -> bool: ...
    async def perceive(self) -> SnapshotResult: ...
    async def act(self, command: MotorCommand) -> ExecutionResult: ...
```

CLI and graph wiring should consume the adapter through this contract, not through adapter-specific startup helpers.

## When to use
Use when adding or refactoring browser runtimes such as BrowserOS or Crawl4AI.

## Verify
Check that adapter startup, health probing, and cleanup live in the adapter class and not in `main.py` or graph nodes.
