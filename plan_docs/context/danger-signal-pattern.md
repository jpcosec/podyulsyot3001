---
type: pattern
domain: ariadne
source: src/automation/ariadne/danger_contracts.py:1
---

# Pill: Danger Signal & Short-Circuit Pattern

## Pattern
Detect high-risk or terminal states (404, 500, CAPTCHA, "Access Denied") in the `observe_node` and short-circuit directly to `human_in_the_loop` or `llm_rescue_agent` without wasting cascade cycles.

## Implementation
```python
# 1. Inside observe_node
danger = ApplyDangerSignals.check(snapshot)
if danger:
    print(f"[❌] Danger Detected: {danger.type}")
    return {
        "session_memory": {**state["session_memory"], "danger_type": danger.type},
        "errors": state.get("errors", []) + [f"DangerDetected: {danger.type}"]
    }

# 2. In orchestrator routing
def route_after_observe(state: AriadneState):
    if state["session_memory"].get("danger_type") in ["captcha", "block"]:
        return "human_in_the_loop"
    if state["session_memory"].get("danger_type") == "http_error":
        return "human_in_the_loop"
    return "execute_deterministic"
```

## When to use
Use in Phase 2 `404-danger-signal.md` and any new CAPTCHA/blocking detection.

## Verify
Verify that the graph skip nodes `execute_deterministic` and `heuristics` when a danger signal is present.
