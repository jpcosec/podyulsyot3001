---
type: pattern
domain: ariadne
source: src/automation/ariadne/graph/nodes/agent.py:1
---

# Pill: Node Implementation Pattern

## Pattern
All LangGraph nodes in Ariadne 2.0 must be `async` functions that accept `AriadneState` and return a **partial** state dictionary.

## Implementation
```python
async def my_feature_node(state: AriadneState, config: RunnableConfig) -> Dict[str, Any]:
    """Short description of node intent."""
    print("--- NODE: My Feature ---")
    
    # 1. Extract what you need
    portal_name = state.get("portal_name")
    memory = state.get("session_memory", {}).copy()
    
    # 2. Perform async work
    try:
        # result = await some_async_call()
        pass
    except Exception as e:
        # 3. Always catch and log to state['errors']
        return {"errors": state.get("errors", []) + [f"FeatureError: {str(e)}"]}
    
    # 4. Return ONLY what changed
    return {
        "session_memory": {**memory, "new_key": "value"},
        "history": state.get("history", []) # if appending messages
    }
```

## When to use
Use for every new node added to `src/automation/ariadne/graph/nodes/`.

## Verify
Ensure the node is wired into `orchestrator.py` and returns a `Dict`.
