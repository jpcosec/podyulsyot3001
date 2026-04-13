---
type: guardrail
law: 2
domain: cli
source: src/automation/main.py:361
---

# Pill: Law 2 — One Browser Per Mission

## Rule
A single `async with adapter` block must wrap the entire graph execution. The browser context is opened once before the graph starts and closed once after it ends. Nodes must never open or close the browser themselves.

## ❌ Forbidden
```python
# inside a graph node — violates Law 2
async def observe_node(state: AriadneState, config: dict):
    async with BrowserOSExecutor() as executor:   # new browser per node!
        snapshot = await executor.take_snapshot()
```

## ✅ Correct
```python
# main.py:361 — correct pattern inside _invoke_graph
async with adapter as active_adapter:
    config["configurable"]["executor"] = active_adapter
    return await theseus.run(initial_state, config)

# inside observe_node — executor already open, just use it
async def observe_node(state: AriadneState, config: dict):
    executor = config.get("configurable", {}).get("executor")
    snapshot = await executor.take_snapshot()   # no open/close here
```

## Verify
```bash
# NOTE: test_single_browser.py is disabled pending test suite realignment. 
# Verify no illegal __aenter__ usage in domain layers:
grep -rn "__aenter__" src/automation/ariadne/
```
