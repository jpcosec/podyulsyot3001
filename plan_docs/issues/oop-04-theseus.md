# OOP 04 — Theseus coordinator

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-02-adapters.md` and `oop-03-cognition.md`. Parallel with `oop-05-delphi.md` and `oop-06-recorder.md`.

### 1. Explanation
Implement `Theseus` as the coordinator by absorbing the logic currently split across `graph/nodes/observe*`, `graph/nodes/execute_deterministic*`, `graph/nodes/apply_local_heuristics*`, and the remaining graph-routing shell. Theseus is deterministic-first, but it is also the runtime coordinator.

### 2. Reference
`src/automation/ariadne/graph/nodes/observe*`, `src/automation/ariadne/graph/nodes/execute_deterministic*`, `src/automation/ariadne/core/actors.py`, `plan_docs/design/browseros-adapter-lifecycle.md`

### 3. Real fix
Coordinator `Theseus` actor absorbing observation, deterministic execution, local heuristics, and LangGraph coordination.

### 4. Steps
**Flow:**
1. `Theseus` boots the mission runtime: adapter, `Labyrinth`, `AriadneThread`, `Recorder`, `Delphi`, and graph state collaborators.
2. `Theseus` owns LangGraph construction and routing. There is no separate behavior-owning `orchestrator.py`.
3. `if not await self.sensor.is_healthy(): return {"errors": ["FatalError: adapter down"]}`.
4. `snapshot = await self.sensor.perceive()`.
5. `room_id = await self.labyrinth.identify_room(snapshot)`.
6. `edge = self.thread.get_next_step(room_id)` — if no usable deterministic path exists, delegate to `Delphi`.
7. `result = await self.motor.act(command)` for deterministic steps.
8. Unknown-land observations and action outcomes are forwarded to `Recorder` so `Labyrinth` and `AriadneThread` can be updated.

**Dependencies:** `Theseus` is the primary runtime owner. `main.py` should only initialize `Theseus` (or a tiny boot wrapper that immediately yields `Theseus`).

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/graph/orchestrator.py::observe_node`, `execute_deterministic_node`, `apply_local_heuristics_node`, `route_after_*`, `create_ariadne_graph` -> absorb into `Theseus` methods and private helpers.
- `src/automation/main.py::run_apply`, `run_scrape`, `_run_graph` -> reduce to boot-time handoff into `Theseus`.
- `src/automation/ariadne/graph/orchestrator.py::_resolve_target`, `_is_target_present_in_snapshot`, `_extract_from_dom`, `_collect_extracted_memory`, `_evaluate_presence`, `_patched_component_key` -> either become `Theseus`/`Labyrinth` private helpers or disappear.

### 5. Test command
1. Unit tests with fake adapter + in-memory `Labyrinth`/`AriadneThread` cover: happy path, unknown room, missing step, motor failure, unhealthy adapter.
2. `Theseus` owns graph coordination; no behavior remains in `graph/orchestrator.py` beyond temporary transition residue.
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
