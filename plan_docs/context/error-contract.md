---
type: model
domain: ariadne
source: src/automation/ariadne/exceptions.py:1
---

# Pill: Error Contract

## Structure
All domain errors must be caught, tagged with `[⚠️]` or `[❌]`, and then re-raised or logged to the `errors` state field.

## Common Exception Types
- `ObservationError`: Failed to capture DOM or screenshot.
- `TranslationError`: Mission resolution failed.
- `DeterministicExecutionError`: Failed to click/fill a static target.
- `HeuristicError`: All local rules failed.

## Implementation (Log & Continue)
```python
try:
    # Some work
    pass
except Exception as e:
    # 1. Log with standard tag
    print(f"[⚠️] MyNodeError: {e}")
    
    # 2. Append to state errors list for the orchestrator to see
    return {"errors": state.get("errors", []) + [f"MyNode: {str(e)}"]}
```

## Implementation (Hard Break)
```python
# Re-raise ONLY if the entire graph cannot continue
raise ObservationError(f"Fatal DOM capture error: {e}") from e
```

## Verify
Verify that the `errors` list contains the logged string in your test assertions.
