---
type: pattern
domain: ariadne
source: plan_docs/design/ariadne-oop-architecture.md:91
---

# Pill: Ariadne Thread Pattern

## Pattern
`AriadneThread` is mission-path memory. It answers "where do I go next from this room for this mission?" and accumulates new successful steps as the system learns.

## Implementation
```python
command = thread.get_next_step(current_room_id)
thread.add_step(edge)
```

Keep mission routing in `AriadneThread`. Do not mix room identification, browser I/O, or LLM rescue logic into this object.

## When to use
Use when implementing deterministic navigation, route lookup, and route assimilation from recordings.

## Verify
Check that deterministic actors query `AriadneThread` for the next step and that recorder/promotion flows update mission steps through this boundary.
