---
type: pattern
domain: scraping
source: plan_docs/design/ariadne-oop-architecture.md:117
---

# Pill: Promotion Pattern (Recording -> Map)

## Pattern
Promotion converts recorded behavior into reusable navigation knowledge. In the new design, promotion should extract topology for `Labyrinth` and mission routes for `AriadneThread`, even if the current persisted artifact is still an `AriadneMap` draft.

## Implementation
```python
events = await recorder.load_events_async(thread_id)
deterministic = [e for e in events if e["source"] == "deterministic"]
draft = promoter.promote_thread(thread_id)
```

## When to use
Use when turning recorded sessions into reusable portal knowledge or validating promoted drafts.

## Verify
Verify only allowed event sources are promoted and the promoted output can be replayed or loaded by repository code.
