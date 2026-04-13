# OOP 05 — Delphi actor (LLM/HITL rescue)

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-02-adapters.md`. Parallel with `oop-04-theseus.md` and `oop-06-recorder.md`.

### 1. Explanation
Implement `Delphi.__call__` by absorbing `graph/nodes/llm_rescue*` and `graph/nodes/hitl*`. Delphi is the expensive rescue path; it must enforce Law 4 circuit breakers.

### 2. Reference
`src/automation/ariadne/graph/nodes/llm_rescue*`, `src/automation/ariadne/graph/nodes/hitl*`, `src/automation/ariadne/core/actors.py`

### 3. Real fix
Rescue `Delphi` actor absorbing `llm_rescue` and `hitl` nodes with circuit breakers.

### 4. Steps
**Flow:**
1. `snapshot = await self.sensor.perceive()`.
2. Build prompt using `state["instruction"]` + `state["current_mission_id"]` + (if present) `state["session_memory"]["hints"]` + annotated screenshot.
3. Circuit breakers (Law 4):
   - ≥2 consecutive LLM parse failures on the same room → escalate to HITL.
   - `session_memory["agent_failures"] >= 3` → escalate to HITL immediately.
4. LLM returns a `MotorCommand` (structured output). Execute via `await self.motor.act(command)`. `result.trace` is appended to `state["trace"]` (tagged `source: "llm_agent"` by `Recorder` downstream). `Delphi` does not call `Recorder` directly.
6. HITL branch: pause the graph and surface a breakpoint for human intervention.

**Dependencies injected:** `sensor`, `motor`, `llm_client`, `hitl_handler`.

### 4.1 Serena AST refactor operations
- `src/automation/ariadne/graph/orchestrator.py::llm_rescue_agent_node` -> absorb into `src/automation/ariadne/core/actors.py::Delphi/__call__` as prompt construction, structured-output parsing, and command execution.
- `src/automation/ariadne/graph/orchestrator.py::human_in_the_loop_node` -> absorb into `src/automation/ariadne/core/actors.py::Delphi/__call__` as the explicit HITL escalation branch.
- Any retry/circuit-breaker state currently threaded through `route_after_heuristics` or `route_after_agent` -> move to `Delphi`-owned counters first, then leave graph routing to consume the normalized state flags in OOP 07.
- After migration, use `find_referencing_symbols` on `llm_rescue_agent_node` and `human_in_the_loop_node` to verify only graph wiring still mentions them before deleting the legacy nodes.

### 5. Test command
1. Unit tests cover: happy LLM resolve, repeated LLM failure → HITL, `agent_failures >= 3` → HITL, prompt includes `instruction` + `mission_id`.
2. `graph/nodes/llm_rescue*` and `graph/nodes/hitl*` are flagged for deletion in OOP 07.
3. No imports from `motors/`. All browser interaction goes through `self.motor`.

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
