---
type: guardrail
law: 2
domain: cli
source: src/automation/main.py:319
---

# Pill: Law 2 — One Browser Per Mission

## Rule
A single `async with executor` block must wrap the entire graph execution. The browser context is opened once before the graph starts and closed once after it ends. Nodes must never open or close the browser themselves.

## ❌ Forbidden
```python
# inside a graph node — violates Law 2
async def observe_node(state: AriadneState, config: dict):
    async with BrowserOSExecutor() as executor:   # new browser per node!
        snapshot = await executor.take_snapshot()
```

## ✅ Correct
```python
# main.py:319 — correct pattern
async with executor as active_executor:
    config["configurable"]["executor"] = active_executor
    async for chunk in app.astream(initial_state, config):
        ...

# inside observe_node — executor already open, just use it
async def observe_node(state: AriadneState, config: dict):
    executor = config.get("configurable", {}).get("executor")
    snapshot = await executor.take_snapshot()   # no open/close here
```

## Verify
```bash
python -m pytest tests/architecture/test_single_browser.py -q
```
Spies on `__aenter__` and asserts it is called exactly once per `app.astream()` invocation.
