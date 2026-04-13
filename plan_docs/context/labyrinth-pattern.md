---
type: pattern
domain: ariadne
source: plan_docs/design/ariadne-oop-architecture.md:85
---

# Pill: Labyrinth Pattern

## Pattern
Use `Labyrinth` as the topology brain. Actors hand it a snapshot, and it decides which known room best matches the current browser state. Exploration and assimilation expand the labyrinth when a new room is discovered.

## Implementation
```python
snapshot = await sensor.perceive()
room_id = labyrinth.identify_room(snapshot)
labyrinth.expand(new_room_data)
```

Keep room matching, state signatures, and topology growth inside `Labyrinth`. Do not mix mission selection, browser actions, or rescue prompting into this object.

## When to use
Use when implementing room identification, new-state discovery, and topology updates in deterministic or recording flows.

## Verify
Check that actors ask `Labyrinth` where they are before choosing a mission step, and that newly discovered rooms are assimilated through `expand(...)` rather than ad-hoc graph state mutations.
