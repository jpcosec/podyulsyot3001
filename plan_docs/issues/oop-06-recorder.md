# OOP 06 — Recorder actor (assimilation)

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-03-cognition.md`. Parallel with `oop-04-theseus.md` and `oop-05-delphi.md`.

### 1. Explanation
Implement `Recorder` as the graph-assimilation service for `Labyrinth` (and related `AriadneThread` updates) by absorbing `src/automation/ariadne/capabilities/recording.py` and `src/automation/ariadne/promotion.py`. All persistence goes through `ariadne/io.py`.

### 2. Reference
`src/automation/ariadne/capabilities/recording.py`, `src/automation/ariadne/promotion.py`, `src/automation/ariadne/io.py`, `plan_docs/design/design_spec.md` §4 "Motor de Asimilación Dual"

### 3. Real fix
Unified `Recorder` assimilation service handling both active and passive trace assimilation.

### 4. Steps
1. `Recorder` updates `Labyrinth` when execution enters unknown land: new URL/state/page-skeleton observations are normalized and written for later querying.
2. `Recorder` updates `AriadneThread` with action outcomes: action -> resulting state/path success/failure (e.g. clicked button -> 404, broken path).
3. `Recorder.__call__(state)` ingests active traces from runtime execution and maps them into both semantic graph updates and path updates.
4. `Recorder.promote(thread_id)` builds/updates canonical `Labyrinth` rooms and `AriadneThread` edges from recorded knowledge.
5. `Recorder.ingest_passive_trace(devtools_json: dict)` still feeds physical traces through the same assimilation pipeline, but human-action recording is a separate concern and not the primary focus of this atom.
6. `capabilities/recording.py` and `promotion.py` shrink to thin shims or are deleted in OOP 07.

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/capabilities/recording.py::GraphRecorder/record_event`, `record_event_async`, `_build_event`, `_trace_path` -> absorb into `Recorder` persistence helpers owned by the `Labyrinth` assimilation service.
- `src/automation/ariadne/capabilities/recording.py::GraphRecorder/load_events`, `load_events_async` -> move into `Recorder` helpers only if still needed for promotion; otherwise replace with `ariadne/io.py` calls and delete.
- `src/automation/ariadne/promotion.py::AriadnePromoter/promote_thread`, `_build_state`, `_substitute_placeholders`, `_write_map` -> absorb into `Recorder` as public/private assimilation methods.
- If Chrome DevTools passive trace ingestion needs separate parsing helpers, add them as private `Recorder` methods rather than a new standalone module.

### 5. Test command
1. Unit tests cover: (a) unknown-land observations become `Labyrinth` updates; (b) action outcomes become `AriadneThread` path updates; (c) a sample passive trace still produces valid semantic/path updates; (d) draft vs canonical status guard works.
2. No direct JSON I/O — all reads/writes via `ariadne/io.py`.
3. `tests/architecture/test_sync_io_detector.py` green.

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Ariadne Shared I/O Pattern](../context/ariadne-io-pattern.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Promotion Pattern (Recording -> Map)](../context/promotion-pattern.md)
- [Graph Recording Pattern](../context/recording-pattern.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
