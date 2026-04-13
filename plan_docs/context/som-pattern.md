---
type: pattern
domain: ariadne
source: src/automation/ariadne/graph/nodes/observe.py:1
---

# Pill: Set-of-Mark (SoM) Pattern

## Pattern
Inject labels into the UI, then capture a screenshot. This ensures the VLM can reference elements by their visual hint (e.g. `[AA]`) instead of complex selectors.

## Implementation
```python
# 1. After take_snapshot(), inject hints
hints = await HintingTool.inject_hints(executor)

# 2. Recapture screenshot (it will contain hints)
state["screenshot_b64"] = await executor.take_snapshot().screenshot_b64

# 3. Save hints dictionary in session_memory
state["session_memory"]["hints"] = hints # map of [AA] -> description
```

## When to use
Use in Phase 3 `set-of-mark-observe.md`.

## Verify
Verify that `session_memory["hints"]` is populated and that the screenshot contains injected overlays.
