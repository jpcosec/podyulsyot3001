---
type: model
domain: ariadne
source: src/automation/ariadne/models.py:161
---

# Pill: AriadneMap Model

## Structure
The `AriadneMap` structure at `models.py:161`:

- `states`: `Dict[str, AriadneStateDefinition]` (Nodes)
- `edges`: `List[AriadneEdge]` (Transitions)
- `success_states`: `List[str]` (Goal states)
- `failure_states`: `List[str]` (Terminal failure states)

`AriadneStateDefinition`:
- `id`: State identifier.
- `presence_predicate`: `AriadneObserve` logic.
- `components`: `Dict[str, AriadneTarget]`.

`AriadneEdge`:
- `from_state` / `to_state`: Connection points.
- `mission_id`: Mission gate.
- `intent`: `AriadneIntent` (click, fill, etc.).
- `target`: `Union[str, AriadneTarget]`.

## Usage
`Labyrinth` and `Theseus` use the map to navigate.

## Verify
`grep -n "class AriadneMap" src/automation/ariadne/models.py`
