# Task: is_mission_complete field + terminal room routing

## Explanation
`builder.py` routing functions only see `AriadneState`. `Labyrinth` is injected into node constructors, not placed in state. This means the router cannot call `room.state.is_terminal` directly, so terminal room detection is currently broken — the graph has no way to exit cleanly when a mission succeeds.

## Reference
- `src/automation/contracts/state.py` — `AriadneState` TypedDict
- `src/automation/langgraph/builder.py` — routing functions (`_route_after_theseus`)
- `src/automation/langgraph/nodes/theseus.py` — knows `room_id`, has access to `Labyrinth`
- `src/automation/ariadne/labyrinth/room_state.py` — `is_terminal: bool` already exists on `RoomState`

## What to fix
Add `is_mission_complete: bool` to `AriadneState`. `TheseusNode` writes it `True` when `labyrinth.get_room(room_id).state.is_terminal`. The router in `builder.py` reads the flag and routes to `END` instead of looping back.

## How to do it
1. Add `is_mission_complete: bool` to `AriadneState` in `contracts/state.py` (default `False`)
2. In `TheseusNode.__call__`, after identifying `room_id`, check `labyrinth.get_room(room_id).state.is_terminal` and include `is_mission_complete: True` in the returned patch if so
3. In `builder.py`, update `_route_after_recorder` (or equivalent) to return `END` when `state["is_mission_complete"]`
4. Add/update tests in `tests/langgraph/nodes/test_theseus.py` and a routing test in `tests/langgraph/`

## Depends on
Nothing — all pieces are in place, only wiring is missing.
