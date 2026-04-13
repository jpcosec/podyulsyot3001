---
type: pattern
domain: scraping
source: src/automation/ariadne/capabilities/recording.py:1
---

# Pill: Graph Recording Pattern

## Pattern
Record every event (URL change, click, fill) to the `AriadneState.history` during a discovery run. This is the source for future "Promotion" to a static map.

## Implementation
```python
# In any node that performs an action
action_event = {
    "type": "click",
    "selector": "#submit",
    "url_after": await executor.get_url(),
    "screenshot_after": await executor.take_snapshot().screenshot_b64
}

# Update history (using add_messages reducer)
return {"history": state.get("history", []) + [action_event]}
```

## When to use
Use in Phase 4 `recording-promoter-guard.md`.

## Verify
Verify that `final_state.history` contains all executed steps in chronological order.
