# OOP 05 — Delphi next-step chooser

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-02-adapters.md`. Parallel with `oop-04-theseus.md` and `oop-06-recorder.md`.

### 1. Explanation
Implement `Delphi` as the next-step chooser used only when no deterministic `AriadneThread` path exists for the current `Labyrinth` position. Delphi may still trigger HITL through circuit breakers, but it is not the general coordinator.

### 2. Reference
`src/automation/ariadne/graph/nodes/llm_rescue*`, `src/automation/ariadne/graph/nodes/hitl*`, `src/automation/ariadne/core/actors.py`

### 3. Real fix
LLM-backed `Delphi` actor choosing the next step when thread guidance is missing.

### 4. Steps
**Flow:**
1. Trigger only when `AriadneThread` has no usable next step for the current room.
2. Collect context: current room/state, local `Labyrinth` vicinity, mission/instruction context, optional hints, and current snapshot.
3. Build the prompt through a LangChain-facing module/client.
4. Circuit breakers (Law 4):
   - repeated parse/decision failures on the same room escalate to HITL
   - `session_memory["agent_failures"] >= 3` escalates immediately
5. Return the chosen next step/command to `Theseus` for coordination and execution, or surface HITL when the circuit breaker trips.

**Dependencies injected:** `sensor`, `motor`, `labyrinth`, LangChain LLM module/client, optional HITL handler.

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/graph/orchestrator.py::llm_rescue_agent_node` -> absorb into `Delphi` as prompt construction and next-step choice logic.
- `src/automation/ariadne/graph/orchestrator.py::human_in_the_loop_node` -> absorb into `Delphi`/`Theseus` coordination as the explicit escalation branch.
- Any retry/circuit-breaker state currently threaded through `route_after_heuristics` or `route_after_agent` -> move to `Delphi`-owned counters and normalized decision outputs.
- After migration, use `find_referencing_symbols` on `llm_rescue_agent_node` and `human_in_the_loop_node` to verify only graph wiring still mentions them before deleting the legacy nodes.

### 5. Test command
1. Unit tests cover: no-thread-path trigger, happy LLM next-step resolve, repeated LLM failure → HITL, `agent_failures >= 3` → HITL, prompt includes current room + vicinity + mission context.
2. `Delphi` does not own general graph coordination; it only decides the next step when deterministic guidance is missing.
3. No imports from `motors/`. All browser interaction goes through injected periphery abstractions.

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Gemini Flash Default LLM](../context/gemini-flash-default.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 4 - Finite Routing](../context/law-4-finite-routing.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Structured Output Pattern (VLM/LLM)](../context/structured-output-pattern.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.
