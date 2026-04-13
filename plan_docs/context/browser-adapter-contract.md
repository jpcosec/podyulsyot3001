---
type: model
domain: scraping
source: src/automation/ariadne/core/periphery.py:56
lifecycle: target
---

# Pill: Browser Adapter Contract

## Structure
`BrowserAdapter` combines browser lifecycle, health, perception, and action contracts behind one injected object.

Required behavior:
- `async def __aenter__(self) -> BrowserAdapter`
- `async def __aexit__(self, exc_type, exc, tb) -> None`
- `async def is_healthy(self) -> bool`
- `async def perceive(self) -> SnapshotResult`
- `async def act(self, command: MotorCommand) -> ExecutionResult`

## Usage
The CLI instantiates one adapter and runs the mission inside `async with adapter:`.

Actors consume the adapter through injected `Sensor` and `Motor` roles, while lifecycle ownership stays inside the adapter implementation.

## Verify
Check that:
- startup and health checks live in the adapter implementation (e.g. `BrowserOSAdapter`)
- CLI does not own adapter polling or launch loops
- graph actors use injected interfaces instead of constructing browser runtimes themselves
