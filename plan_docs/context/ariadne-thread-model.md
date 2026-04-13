---
type: model
domain: ariadne
source: plan_docs/design/ariadne-oop-architecture.md:91
---

# Pill: Ariadne Thread Model

## Structure
`AriadneThread` is the mission-path memory object. It stores the directed steps that define how a specific mission moves from room to room.

Core responsibilities:
- store mission-scoped transitions
- answer the next deterministic step for a known room
- accept newly learned steps from recording/promotion flows

Core interface shape:
- `get_next_step(current_room_id: str) -> Command`
- `add_step(edge) -> None`

## Usage
`Theseus` asks `AriadneThread` for the next step once the current room is identified. `Recorder` and promotion flows extend the thread as new successful routes are discovered.

Treat `AriadneThread` as "where do I go next for this mission?" memory. Room identification belongs to `Labyrinth`.

## Verify
Check that mission routing state lives on `AriadneThread` and is not duplicated in CLI code, adapters, or room-identification logic.
