# OOP 03 — Labyrinth + AriadneThread (active memory)

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-01-scaffold.md`. Parallel with `oop-02-adapters.md`.

### 1. Explanation
Fill in `core/cognition.py` and absorb `src/automation/ariadne/repository.py` persistence into `Labyrinth.load_from_db` / `AriadneThread.load_from_db`. All JSON/JSONL routing goes through `ariadne/io.py`.

### 2. Reference
`src/automation/ariadne/repository.py`, `src/automation/ariadne/io.py`, `src/automation/ariadne/models.py`, `plan_docs/design/ariadne-oop-architecture.md`

### 3. Real fix
`Labyrinth` and `AriadneThread` classes with async persistence via `ariadne/io.py`.

### 4. Steps
1. `Labyrinth`
   - State: dict of `StateDefinition` rooms + predicates (CSS/XPath/heuristic).
   - `async identify_room(snapshot: SnapshotResult) -> str | None` — evaluates predicates against the snapshot.
   - `expand(room_data) -> None` — adds a new room/predicate.
   - `async classmethod load_from_db(portal: str) -> Labyrinth` — reads via `ariadne/io.py`.
   - Raises `MapNotFoundError` when no map exists (see `zero-shot-error-typing.md`).
2. `AriadneThread`
   - State: ordered list of transitions per mission.
   - `get_next_step(current_room_id) -> MotorCommand | None`.
   - `add_step(edge) -> None`.
   - `available_missions() -> list[str]` (for `Interpreter`).
   - `async classmethod load_from_db(portal, mission)`.
3. `repository.py` shrinks to a thin backwards-compat shim (or is deleted if nothing else imports it). No direct JSON I/O outside `ariadne/io.py`.
4. Heuristics currently in `graph/nodes/apply_local_heuristics*` become `Labyrinth` predicates (they are room-identification rules, not a separate pipeline stage).

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/repository.py::MapRepository/get_map`, `_load_map_async`, `get_map_async`, `_load_map_sync` -> split between `src/automation/ariadne/core/cognition.py::Labyrinth/load_from_db` and `src/automation/ariadne/core/cognition.py::AriadneThread/load_from_db`.
- `src/automation/ariadne/repository.py::_cache_key` -> either fold into a small private helper inside `Labyrinth`/`AriadneThread` or delete if the new `ariadne/io.py` pathing makes it redundant.
- `src/automation/ariadne/graph/orchestrator.py::apply_local_heuristics_node` -> extract room-identification predicates and move them into `src/automation/ariadne/core/cognition.py::Labyrinth/identify_room` or `Labyrinth.expand`, leaving routing concerns for OOP 07.
- Use `find_referencing_symbols` on `MapRepository` before deleting the class; any survivors outside `core/cognition.py` become explicit shim callers or follow-up cleanup work for OOP 08.

### 5. Test command
1. `Labyrinth` / `AriadneThread` unit tests cover: load, identify_room, get_next_step, MapNotFoundError.
2. No call to `open()` or synchronous `json.load()` inside `core/cognition.py`.
3. `tests/architecture/test_sync_io_detector.py` green.
4. `graph/nodes/apply_local_heuristics*` logic either absorbed into `Labyrinth` predicates or flagged for deletion in OOP 07.

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Ariadne Shared I/O Pattern](../context/ariadne-io-pattern.md)
- [Labyrinth Model](../context/labyrinth-model.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Ariadne Thread Model](../context/ariadne-thread-model.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
