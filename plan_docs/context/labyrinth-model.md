---
type: model
domain: ariadne
source: plan_docs/design/ariadne-oop-architecture.md:81
---

# Pill: Labyrinth Model

## Structure
`Labyrinth` is the topological memory object. It stores known rooms/states and the structural clues used to identify the current room from a snapshot.

Core responsibilities:
- identify the current room from `SnapshotResult`
- store and expand discovered rooms
- answer topology questions without owning mission intent

## Usage
`Theseus` asks `Labyrinth.identify_room(snapshot)` before choosing an action. `Recorder` calls `Labyrinth.expand(room_data)` when exploration discovers a new room.

Treat `Labyrinth` as "where am I?" memory. Mission routing belongs elsewhere.

## Visual

```
                  ┌─────────────────────── Labyrinth (portal=linkedin) ───────────────────────┐
                  │                                                                           │
                  │         ┌────────────┐                                                    │
                  │         │  home      │  predicate: url contains "/home"                   │
                  │         │  (room_A)  │                                                    │
                  │         └─────┬──────┘                                                    │
                  │               │                                                           │
                  │        ┌──────┴──────┐                                                    │
                  │        ▼             ▼                                                    │
                  │  ┌──────────┐  ┌──────────────┐                                           │
                  │  │ search    │  │ job_listing │  predicate: dom has "[data-job-card]"     │
                  │  │ (room_B)  │  │ (room_C)    │                                           │
                  │  └─────┬────┘  └──────┬───────┘                                           │
                  │        │              │                                                    │
                  │        ▼              ▼                                                    │
                  │  ┌──────────┐  ┌──────────────┐                                           │
                  │  │ results  │  │ easy_apply   │  predicate: dom has "button[aria-label='Apply']"
                  │  │ (room_D) │  │ (room_E)     │                                           │
                  │  └──────────┘  └──────┬───────┘                                           │
                  │                        │                                                   │
                  │                        ▼                                                   │
                  │                  ┌──────────────┐                                          │
                  │                  │ apply_form   │                                          │
                  │                  │ (room_F)     │                                          │
                  │                  └──────────────┘                                          │
                  └───────────────────────────────────────────────────────────────────────────┘

AriadneThread (mission=easy_apply)  overlays this labyrinth with an ordered edge sequence:
    home → job_listing → easy_apply → apply_form → submit

AriadneThread (mission=discovery) overlays the SAME labyrinth with a DIFFERENT sequence:
    home → search → results → [extract jobs]
```

Rooms are nodes with predicates (CSS/XPath/heuristic). `identify_room(snapshot)` evaluates predicates against the current `SnapshotResult` and returns the matching room's id. Edges belong to `AriadneThread`, not `Labyrinth` — the labyrinth knows the map of rooms, the thread knows which sequence of rooms to visit for a given mission.

## Verify
Check that room identification and room expansion logic live on `Labyrinth`, not in CLI wiring or actor prompt code. Check that edges/transitions live on `AriadneThread`, not on `Labyrinth` — the labyrinth is a room catalog, not a route.
