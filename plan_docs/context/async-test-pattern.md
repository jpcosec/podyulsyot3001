---
type: pattern
domain: architecture
source: tests/unit/automation/ariadne/test_orchestrator.py:1
---

# Pill: Async Test Pattern (LangGraph)

## Pattern
Test LangGraph nodes and orchestrator by streaming updates through `app.astream()`. This ensures reducers and routing are fully exercised.

## Implementation
```python
@pytest.mark.asyncio
async def test_my_feature_node():
    # 1. Setup minimal state
    initial_state = {
        "instruction": "test",
        "portal_name": "example",
        "session_memory": {},
        "errors": [],
        # ... other required AriadneState fields
    }
    
    # 2. Setup executor and config
    executor = MyMockExecutor() # or real Crawl4AIExecutor
    config = {"configurable": {"thread_id": "test", "executor": executor}}
    
    # 3. Stream and assert
    async with create_ariadne_graph() as app:
        async for chunk in app.astream(initial_state, config):
            for node_name, state_update in chunk.items():
                if node_name == "my_target_node":
                    assert "new_key" in state_update["session_memory"]
```

## When to use
Use for every feature addition in `tests/unit/automation/ariadne/` and all Phase 0/2 integration tests.

## Verify
Run `python -m pytest path/to/test.py -v`
