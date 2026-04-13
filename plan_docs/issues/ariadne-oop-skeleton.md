# Ariadne OOP Skeleton (Umbrella — Atomized)

**Status:** Umbrella. Do not execute directly. Each atom below is a standalone executable issue.

**Goal:** Introduce the canonical OOP skeleton (Sensor/Motor/BrowserAdapter, Labyrinth/AriadneThread, Theseus/Delphi/Recorder/Interpreter), move all graph behavior under the owning classes, and absorb existing modules into the class that owns them. Leave no parallel function-style path behind.

**Design references:**
- `plan_docs/design/design_spec.md` (especially §4 "Motor de Asimilación Dual")
- `plan_docs/design/ariadne-oop-architecture.md`
- `plan_docs/design/browseros-adapter-lifecycle.md`

**External reference:** Chrome DevTools Recorder — https://developer.chrome.com/docs/devtools/recorder. `Recorder` consumes two input sources that land in the same assimilation pipeline: active traces from `Theseus`/`Delphi` (tagged `deterministic`/`llm_agent`) and passive `.json` exports from Chrome DevTools Recorder (physical human sessions). See `oop-06-recorder.md` for details.

**Laws of Physics (non-negotiable across every atom):**
1. **Law 1:** all new methods `async`. Persistence only through `ariadne/io.py`.
2. **Law 2:** exactly one `BrowserAdapter` per mission, instantiated once during `Theseus` boot for that mission, then reused everywhere.
3. **Law 3:** DOM injection stays on overlays.
4. **Law 4:** `Delphi` enforces circuit breakers (2 LLM retries → HITL after 3 agent failures).
5. **DIP:** `core/` must NOT import from `src/automation/motors/`.

## Atoms

Execution order and parallelism:

```
oop-01-scaffold
    ├── oop-02-adapters   ─┐
    └── oop-03-cognition  ─┤
                           ├── oop-04-theseus   ─┐
                           ├── oop-05-delphi    ─┤
                           └── oop-06-recorder  ─┤
                                                 └── oop-07-graph-wiring
                                                              └── oop-08b-package-locality
                                                                          └── oop-08-cleanup
```

1. [`oop-01-scaffold.md`](oop-01-scaffold.md) — create empty `core/` package (protocols, ABCs, stubs). No behavior. **Blocks everything below.**
2. [`oop-02-adapters.md`](oop-02-adapters.md) — `BrowserOSAdapter` + `Crawl4AIAdapter`, absorbing BrowserOS lifecycle from `main.py`. Parallel with 03.
3. [`oop-03-cognition.md`](oop-03-cognition.md) — `Labyrinth` + `AriadneThread`, absorbing `repository.py`. Parallel with 02.
4. [`oop-04-theseus.md`](oop-04-theseus.md) — `Theseus` becomes the coordinator, absorbing `observe*` + `execute_deterministic*` + `apply_local_heuristics*` nodes and owning LangGraph coordination. Parallel with 05, 06.
5. [`oop-05-delphi.md`](oop-05-delphi.md) — `Delphi` becomes the next-step chooser when no deterministic `AriadneThread` path exists. Parallel with 04, 06.
6. [`oop-06-recorder.md`](oop-06-recorder.md) — `Recorder` becomes the graph-assimilation service for `Labyrinth`, absorbing `capabilities/recording.py` + `promotion.py`. Parallel with 04, 05.
7. [`oop-07-graph-wiring.md`](oop-07-graph-wiring.md) — delete `graph/orchestrator.py`; move remaining graph construction under `Theseus` and slim `main.py` to boot only.
8. [`oop-08b-package-locality.md`](oop-08b-package-locality.md) — relocate contracts/models/io/config/hints toward their owning packages using a two-tier contract rule.
9. [`oop-08-cleanup.md`](oop-08-cleanup.md) — delete absorbed modules, convert `modes/*` to injected strategies, update `ariadne/README.md`.

## Oversized file migration map

Use this as the top-level Phase 0.5 ownership table when a file or function is too large and appears to mix concerns. The intended split is by owning class, not by preserving legacy file boundaries.

### `src/automation/main.py`
- CLI surface stays in `main.py`: `_build_parser`, `_default_profile`, `_load_profile`, thin input translation, and boot-only command dispatch.
- Browser lifecycle moves to `core/adapters/browseros.py::BrowserOSAdapter`: `_check_browseros_running`, `_launch_browseros`, `_ensure_browseros`.
- Executor lifecycle moves to concrete adapters: `BrowserOSCliExecutor/*` -> `BrowserOSAdapter`, `Crawl4AIExecutor/*` -> `Crawl4AIAdapter`.
- `main.py` should only initialize `Theseus` (or a tiny boot object that immediately yields `Theseus`) and hand over control.
- Rule of thumb: if any top-level helper in `main.py` grows beyond simple CLI translation or bootstrapping, it should move into `Theseus` or another owner.

### `src/automation/ariadne/graph/orchestrator.py`
- `observe_node` + `execute_deterministic_node` + `apply_local_heuristics_node` -> `Theseus` and its private helpers.
- `llm_rescue_agent_node` + `human_in_the_loop_node` -> `Delphi` and `Theseus` coordination helpers.
- `create_ariadne_graph` + `route_after_*` functions do not survive as a separate module; graph construction moves under `Theseus`.
- Helper functions under deterministic execution (`_resolve_target`, `_is_target_present_in_snapshot`, `_extract_from_dom`, `_collect_extracted_memory`, `_evaluate_presence`, `_patched_component_key`) either become actor/cognition-private helpers or disappear.
- End state: `src/automation/ariadne/graph/orchestrator.py` is deleted.

### `src/automation/ariadne/repository.py`
- `MapRepository/*` -> `core/cognition.py::Labyrinth.load_from_db` and `core/cognition.py::AriadneThread.load_from_db`.
- `repository.py` may remain temporarily only as a compatibility shim until OOP 08 removes it.

### `src/automation/ariadne/capabilities/recording.py`
- `GraphRecorder/*` -> `Recorder` persistence helpers in service of `Labyrinth` graph assimilation.

### `src/automation/ariadne/promotion.py`
- `AriadnePromoter/*` -> `Recorder` assimilation/build methods and related private helpers.

## Ownership clarifications

- `Theseus` is the coordinator. It owns LangGraph coordination, initializes runtime collaborators for a mission, and drives the deterministic-first flow.
- `Delphi` is not a general rescue bucket. It decides the next step only when no usable `AriadneThread` path exists for the current `Labyrinth` position.
- `Labyrinth` is the semantic graph over URL, state, and page skeleton abstractions.
- `AriadneThread` stores task-specific flows over the `Labyrinth` and owns deterministic path reading.
- `Recorder` is the graph-assimilation service for `Labyrinth` (and related `AriadneThread` updates). It records unknown-land discoveries and action outcomes so they can be written back for later querying.

### Size-to-shape heuristic for Phase 0.5
- Any legacy file over ~200 lines is a migration candidate, but the real trigger is mixed ownership across adapters, cognition, actors, and graph wiring.
- Any single function or method over ~200 lines should be split into class-owned private helpers even if the destination file remains under one class.
- Large classes are acceptable only when they preserve one actor boundary (`Theseus`, `Delphi`, `Recorder`, `BrowserAdapter`, `Labyrinth`, `AriadneThread`) and do not mix CLI, persistence, browser lifecycle, and graph wiring.

## Package locality rule

Phase 0.5 uses a two-tier rule for code placement:

- Tier 1: owner-local code by default. Contracts, models, helpers, and storage APIs live next to the class or subsystem that owns them.
- Tier 2: a very small central contract layer is allowed only for DTOs that genuinely cross multiple owner boundaries and would otherwise create duplication or import cycles.
- `io.py` is not a generic top-level utility. Persistence belongs under owner-specific or shared storage modules.
- `config.py` is runtime infrastructure, not a domain utility. Actors should consume injected values; runtime/periphery may read config during construction/bootstrap.
- Hinting belongs with `Delphi`/rescue cognition unless a later phase proves it is a stable cross-actor boundary.

## Umbrella-level acceptance criteria
All of the following must hold after atom 08 closes:

1. `src/automation/ariadne/core/` exists with split actor/cognition owners and adapter implementations.
2. `graph/orchestrator.py` is gone; graph construction lives under `Theseus`.
3. `main.py` contains no BrowserOS polling, AppImage launching, `/mcp` probing, or graph coordination logic.
4. `grep -R "from src.automation.motors" src/automation/ariadne/core` returns nothing.
5. `python -m pytest tests/unit/automation/ tests/architecture/ -q` green.
6. `plan_docs/issues/Index.md` reflects all nine atoms as closed.
