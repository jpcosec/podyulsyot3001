---
type: model
domain: ariadne
source: src/automation/ariadne/models.py:161
---

# Pill: AriadneMap Model

## Structure
`AriadneMap` is the directed state graph representing a portal flow.

- `states`: `Dict[str, AriadneStateDefinition]` (Nodes)
- `edges`: `List[AriadneEdge]` (Transitions)
- `success_states`: `List[str]` (Goal nodes)
- `failure_states`: `List[str]` (Terminal failure nodes)

`AriadneStateDefinition` fields:
- `id`: Unique state identifier.
- `presence_predicate`: `AriadneObserve` (Logic to identify this state).
- `components`: `Dict[str, AriadneTarget]` (Semantic elements in this state).

`AriadneEdge` fields:
- `from_state` / `to_state`: Edge endpoints.
- `mission_id`: Optional gate (e.g., 'easy_apply').
- `intent`: Action type (click, fill, etc.).
- `target`: Component name or explicit `AriadneTarget`.

## Usage
`Labyrinth` uses `AriadneMap` to resolve "Where am I?" and "What is here?".

## Verify
`grep "class AriadneMap" src/automation/ariadne/models.py`
