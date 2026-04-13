---
type: model
domain: ariadne
source: plan_docs/issues/Index.md:Phase 1
---

# Pill: Interpreter Node

## Structure
`Interpreter` is the cognitive entry point of the LangGraph.

Responsibilities:
- Transform raw user `instruction` into a concrete `mission_id`.
- Determine if the mission has a known `AriadneThread` (Fast Path) or requires exploration (Slow Path).
- Initialize `AriadneState` with the target `mission_id`.

## Usage
The graph enters through `Interpreter`. It populates `state['current_mission_id']` which `Theseus` and `Delphi` then use to load relevant memory.

## Verify
`python -m pytest tests/unit/automation/ariadne/graph/nodes/test_interpreter.py`
