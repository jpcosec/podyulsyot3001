# OOP 07 — Delete orchestrator.py + boot-only main.py

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-04-theseus.md`, `oop-05-delphi.md`, `oop-06-recorder.md`.

### 1. Explanation
Delete `src/automation/ariadne/graph/orchestrator.py`, move any remaining graph construction under `Theseus`, and slim `src/automation/main.py` to boot only.

### 2. Reference
`src/automation/ariadne/graph/orchestrator.py`, `src/automation/main.py`, `src/automation/ariadne/core/actors/theseus.py`, `plan_docs/design/ariadne-oop-architecture.md`

### 3. Real fix
Complete migration of graph construction into `Theseus`, with `main.py` reduced to startup and handoff.

### 4. Steps
1. `Theseus.build_graph(...) -> CompiledGraph`
   - `Theseus` owns graph construction and routing.
   - `AriadneThread` supplies deterministic path reading.
   - `Delphi` is only invoked when no usable deterministic path exists.
   - `Recorder` is invoked to assimilate unknown-land observations and action outcomes into `Labyrinth` / `AriadneThread`.
2. `main.py` becomes:
    ```python
    async def run(args):
        theseus = await build_theseus_from_args(args)
        await theseus.run(...)
    ```
3. Delete `graph/orchestrator.py` and any leftover `graph/nodes/` function files that are now absorbed (`observe*`, `execute_deterministic*`, `apply_local_heuristics*`, `llm_rescue*`, `hitl*`, `agent.py`). No re-exports.

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/graph/orchestrator.py::create_ariadne_graph` and `route_after_*` -> absorb into `Theseus` methods/private helpers.
- `src/automation/main.py::run_apply`, `run_scrape`, `_run_graph` -> rewire to boot `Theseus` and immediately hand over control.
- `src/automation/main.py::_build_apply_state` and `_build_scrape_state` stay in `main.py` only if they remain pure CLI-to-state translators.
- After rewiring, use `find_referencing_symbols` over each legacy graph node function and delete `graph/orchestrator.py` once references are gone.

### 5. Test command
1. Graph construction lives under `Theseus`, not in a separate orchestrator module.
2. `main.py` LOC drops substantially; `grep "browseros\|appimage\|mcp" src/automation/main.py` returns nothing and `main.py` contains no graph coordination logic.
3. `grep -R "from src.automation.ariadne.graph.nodes" src/` returns nothing, and `src/automation/ariadne/graph/orchestrator.py` no longer exists.
4. `python -m pytest tests/unit/automation/ tests/architecture/ -q` green.

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Ariadne LangGraph](../context/ariadne-langgraph.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 4 - Finite Routing](../context/law-4-finite-routing.md)
- [Ariadne State & Models](../context/ariadne-models.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.
