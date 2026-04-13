# OOP 07 — Graph DI Wiring + main.py slimming

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-04-theseus.md`, `oop-05-delphi.md`, `oop-06-recorder.md`.

### 1. Explanation
Rewrite `src/automation/ariadne/graph/orchestrator.py` to build the graph via constructor injection of the new actors, and slim `src/automation/main.py` to a bare adapter + graph invocation.

### 2. Reference
`src/automation/ariadne/graph/orchestrator.py`, `src/automation/main.py`, `plan_docs/design/ariadne-oop-architecture.md` (LangGraph Wiring Example)

### 3. Real fix
Complete DI rewrite of `orchestrator.py` and `main.py` using new actors.

### 4. Steps
1. `build_graph(adapter, labyrinth, thread, llm_client, hitl_handler) -> CompiledGraph`
   - Instantiate `Theseus`, `Delphi`, `Recorder`, `Interpreter` with injected deps.
   - Register each as a node. Entry point: `Interpreter`.
   - Edges: `Interpreter → Theseus`, `Theseus → {Theseus, Delphi, Recorder, END}` conditional, `Delphi → {Theseus, HITL, END}` conditional, all successful steps emit to `Recorder`.
2. `main.py` becomes:
   ```python
   async def run(args):
       adapter = build_adapter(args.portal, args.motor)
       labyrinth = await Labyrinth.load_from_db(args.portal)
       thread = await AriadneThread.load_from_db(args.portal, args.mission or "")
       async with adapter:
           graph = build_graph(adapter, labyrinth, thread, llm_client, hitl)
           await graph.ainvoke({"instruction": args.instruction, ...})
   ```
3. Delete `graph/nodes/` function files that are now absorbed (`observe*`, `execute_deterministic*`, `apply_local_heuristics*`, `llm_rescue*`, `hitl*`, `agent.py`). No re-exports.

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/graph/orchestrator.py::create_ariadne_graph` -> replace with a DI-only builder that instantiates `Theseus`, `Delphi`, `Recorder`, and `Interpreter` and wires conditional edges.
- `src/automation/ariadne/graph/orchestrator.py::route_after_observe`, `route_after_deterministic`, `route_after_heuristics`, `route_after_agent` -> keep only if they still express graph transitions; otherwise collapse them into smaller routing helpers attached to the new builder.
- `src/automation/main.py::run_apply`, `run_scrape`, `_run_graph` -> rewire to build adapters/cognition objects, enter `async with adapter`, and invoke the graph without BrowserOS lifecycle logic.
- `src/automation/main.py::_build_apply_state` and `_build_scrape_state` stay in `main.py` only if they remain pure CLI-to-state translators; if they grow orchestration behavior, extract a new class instead of leaving more top-level functions behind.
- After rewiring, use `find_referencing_symbols` over each legacy graph node function and delete any node module whose only remaining references were in the old builder.

### 5. Test command
1. `build_graph` takes exactly these DI arguments — no globals, no `config["configurable"]` at call time.
2. `main.py` LOC drops substantially; `grep "browseros\|appimage\|mcp" src/automation/main.py` returns nothing.
3. `grep -R "from src.automation.ariadne.graph.nodes" src/` returns nothing outside the orchestrator (or nothing at all once deleted).
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
