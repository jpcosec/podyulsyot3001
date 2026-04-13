# OOP 04 — Theseus actor (fast path)

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-02-adapters.md` and `oop-03-cognition.md`. Parallel with `oop-05-delphi.md` and `oop-06-recorder.md`.

### 1. Explanation
Implement `Theseus.__call__` by absorbing the logic currently split across `graph/nodes/observe*` and `graph/nodes/execute_deterministic*`. Theseus is the deterministic, zero-cost fast path.

### 2. Reference
`src/automation/ariadne/graph/nodes/observe*`, `src/automation/ariadne/graph/nodes/execute_deterministic*`, `src/automation/ariadne/core/actors.py`, `plan_docs/design/browseros-adapter-lifecycle.md`

### 3. Real fix
Deterministic `Theseus` actor absorbing `observe` and `execute_deterministic` nodes.

### 4. Steps
**Flow (inside `Theseus.__call__`):**
1. `if not await self.sensor.is_healthy(): return {"errors": ["FatalError: adapter down"]}`.
2. `snapshot = await self.sensor.perceive()`.
3. Danger check — if snapshot matches `NavigationDangerSignals` (404/403/500, see `404-danger-signal.md`), return `{"danger_type": "http_error"}` and let routing escalate.
4. `room_id = await self.labyrinth.identify_room(snapshot)` — unknown room → delegate to `Delphi`.
5. `command = self.thread.get_next_step(room_id)` — no command → delegate to `Delphi`.
6. `result = await self.motor.act(command)` — on failure, attach error and delegate to `Delphi`. `result.trace` (a `TraceEvent` fragment returned by `Motor.act()`) is appended to `state["trace"]` via the reducer. `Recorder` consumes `state["trace"]` in a later node — `Theseus` does not call `Recorder` directly.

**Dependencies injected via constructor:** `sensor`, `motor`, `labyrinth`, `thread`. No `config["configurable"]` reads at call time.

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/graph/orchestrator.py::observe_node` -> absorb into `src/automation/ariadne/core/actors.py::Theseus/__call__` as the health-check + snapshot acquisition opening sequence.
- `src/automation/ariadne/graph/orchestrator.py::execute_deterministic_node` -> absorb into `src/automation/ariadne/core/actors.py::Theseus/__call__` as room lookup, command resolution, motor execution, and trace emission.
- `src/automation/ariadne/graph/orchestrator.py::_resolve_target`, `_is_target_present_in_snapshot`, `_extract_from_dom`, `_collect_extracted_memory` -> either become private helpers colocated with `Theseus` or are eliminated if the adapter contracts already cover the same data path.
- `src/automation/ariadne/graph/orchestrator.py::_evaluate_presence` and `_patched_component_key` -> move only if still required by deterministic execution; otherwise leave for OOP 07 cleanup after `find_referencing_symbols` shows no non-routing callers.

### 5. Test command
1. Unit tests with fake adapter + in-memory Labyrinth/Thread cover: happy path, unknown room, missing step, motor failure, unhealthy adapter.
2. `graph/nodes/observe*` and `graph/nodes/execute_deterministic*` are flagged for deletion in OOP 07 (no remaining callers after this issue).
3. Law 1 + Law 2 compliant (async, single adapter).

### 📦 Required Context Pills
- [Danger Signal & Short-Circuit Pattern](../context/danger-signal-pattern.md)
- [DIP Enforcement](../context/dip-enforcement.md)
- [Labyrinth Model](../context/labyrinth-model.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 3 - DOM Hostility](../context/law-3-dom-hostility.md)
- [Ariadne State & Models](../context/ariadne-models.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 3 (DOM Hostility):** All JS injection must use an isolated overlay. Do not mutate existing DOM nodes or event listeners.
