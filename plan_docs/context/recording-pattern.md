---
type: pattern
domain: scraping
source: plan_docs/design/ariadne-oop-architecture.md:117
---

# Pill: Graph Recording Pattern

## Pattern
Recording is an assimilation step, not just history accumulation. `Recorder` captures deterministic and exploratory actions, persists raw trace artifacts through the shared Ariadne I/O layer, and feeds newly discovered structure back into memory.

## Implementation
```python
event = {"source": "deterministic", "payload": payload}
await append_jsonl_async(trace_path, event)
labyrinth.expand(room_data)
thread.add_step(edge)
```

## When to use
Use for trace capture, session recording, and any feature that learns from executed browser actions.

## Verify
Verify the raw trace is persisted, new rooms/steps are assimilated, and promotion can consume the resulting recording.
