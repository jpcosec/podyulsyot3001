# OOP 06 — Recorder actor (assimilation)

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-03-cognition.md`. Parallel with `oop-04-theseus.md` and `oop-05-delphi.md`.

### 1. Explanation
Implement `Recorder.__call__` plus `Recorder.promote()` by absorbing `src/automation/ariadne/capabilities/recording.py` and `src/automation/ariadne/promotion.py`. All persistence goes through `ariadne/io.py`.

### 2. Reference
`src/automation/ariadne/capabilities/recording.py`, `src/automation/ariadne/promotion.py`, `src/automation/ariadne/io.py`, `plan_docs/design/design_spec.md` §4 "Motor de Asimilación Dual"

### 3. Real fix
Unified `Recorder` actor handling both active and passive trace assimilation.

### 4. Steps
1. `Recorder.__call__(state)` — read `state["trace"]` (populated by `Motor.act()` → `ExecutionResult.trace`), tag each event with `source: "deterministic" | "heuristic" | "llm_agent"`, append to `raw_timeline.jsonl` via `ariadne/io.py` async helpers. **`Motor` must NOT hold a reference to `Recorder`** — all coupling goes through state.
2. `Recorder.promote(thread_id)` — build canonical `Labyrinth` rooms and `AriadneThread` edges from deterministic events only. Store LLM events as observations on rooms, never as canonical edges (see `recording-promoter-guard.md`).
3. `Recorder.ingest_passive_trace(devtools_json: dict)` — parse a Chrome DevTools Recorder export (`steps: [{type, selectors, value, ...}]`, see https://developer.chrome.com/docs/devtools/recorder/reference) and feed it through the same pipeline as active traces. Physical click/change steps become candidate `AriadneThread` edges; literal profile values (email, name, etc.) are matched against the active user profile and replaced with `{{...}}` templates.
4. Variable templating (`{{email}}`, `{{profile.first_name}}`) stays where it is but now flows through `Recorder`.
5. `capabilities/recording.py` and `promotion.py` shrink to thin shims or are deleted in OOP 07.

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/capabilities/recording.py::GraphRecorder/record_event`, `record_event_async`, `_build_event`, `_trace_path` -> absorb into `src/automation/ariadne/core/actors.py::Recorder/__call__` or small private helpers owned by `Recorder`.
- `src/automation/ariadne/capabilities/recording.py::GraphRecorder/load_events`, `load_events_async` -> move into `Recorder` helpers only if still needed for promotion; otherwise replace with `ariadne/io.py` calls and delete.
- `src/automation/ariadne/promotion.py::AriadnePromoter/promote_thread`, `_build_state`, `_substitute_placeholders`, `_write_map` -> absorb into `src/automation/ariadne/core/actors.py::Recorder` with `promote()` as the public orchestration method.
- If Chrome DevTools passive trace ingestion needs separate parsing helpers, add them as private `Recorder` methods rather than a new standalone module.

### 5. Test command
1. Unit tests cover: (a) mixed deterministic + LLM events → only deterministic become edges; (b) a sample Chrome DevTools Recorder `.json` export produces a valid `Labyrinth` + `AriadneThread` with templated variables; (c) draft vs canonical status guard works.
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
