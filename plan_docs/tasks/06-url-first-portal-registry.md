# Task 06: URL-first portal registry — dynamic Labyrinth/Thread per domain

## Explanation
Currently `portal_name` is a CLI argument baked into the graph at construction time.
`TheseusNode` and `RecorderNode` hold fixed `Labyrinth` + `AriadneThread` references.
This means the system can only operate within one pre-declared portal per session.

The goal: any URL the browser lands on becomes a portal automatically. The system builds
its map as it navigates and can cross domain boundaries without restarting.

## What to change

### 1. `AriadneState` — add `domain` field
- `domain: str` derived from the live URL's netloc (e.g. `"emol.com"`)
- Written by `ObserveNode` each turn from `snapshot.url`

### 2. `PortalRegistry` — new file `src/automation/ariadne/portal_registry.py`
- `PortalRegistry(mission_id: str)`
- `get(domain) -> (Labyrinth, AriadneThread)` — lazy load, cached in `_portals: dict`
- `save(domain)` — persists both objects for that domain

### 3. `ObserveNode` — derive and emit `domain`
- After `perceive()`, extract netloc from `snapshot.url`
- Add `{"domain": domain}` to return dict

### 4. `TheseusNode` — switch from fixed refs to registry
- Constructor: `(motor, registry, extractor=None)` — drop `labyrinth`, `thread`
- Each call: `labyrinth, thread = self._registry.get(state["domain"])`

### 5. `RecorderNode` — switch from fixed refs to registry
- Constructor: `(registry,)` — drop `labyrinth`, `thread`
- Each call: load from registry, save via `registry.save(domain)`

### 6. `builder.py` — create shared `PortalRegistry`, pass to nodes
- Remove fixed `Labyrinth.load(portal_name)` and `AriadneThread.load(...)` calls
- Seed initial `portal_name` in state so `Interpreter` still works

## Depends on
- Nothing new — `Labyrinth.load()` and `AriadneThread.load()` already handle missing files
- `data/portals/{domain}/` directory auto-created by `save()` (`mkdir parents=True`)

## Tests to add/update
- `tests/langgraph/nodes/test_observe.py` — assert `domain` in returned dict
- `tests/langgraph/nodes/test_theseus.py` — pass mock registry instead of labyrinth/thread
- `tests/langgraph/nodes/test_recorder.py` — same
- New: `tests/ariadne/test_portal_registry.py` — lazy load, cache hit, save
