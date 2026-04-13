# Interpreter: Instruction → mission_id Resolver

**Umbrella:** depends on `ariadne-oop-skeleton.md`. Runs after the OOP skeleton lands.

**Explanation:** The graph must resolve a natural-language instruction to a `mission_id` before any navigation. Under the new OOP design this lives as a dedicated actor (or a method on the entry actor) that `Theseus` consults — not as a free function in `graph/nodes/`.

**Reference:** `src/automation/ariadne/core/actors.py` (new), `src/automation/ariadne/core/cognition.py` (new, `AriadneThread.available_missions`), `src/automation/ariadne/models.py` (`AriadneState`)

**What to fix:** Add an `Interpreter` actor callable that:
- Fast path: exact match between `state["instruction"]` and an available `mission_id` exposed by `AriadneThread` → return it without an LLM call.
- Slow path: Gemini Flash with structured output (`MissionResolution` pydantic model: `mission_id`, `dry_run`) to map free text to a known mission.
- Fallback: `MapNotFoundError` (see `zero-shot-error-typing.md`) → `mission_id = "explore"`.

Wire it as the graph entry point via constructor injection in `build_graph()`; `main.py` seeds `state["instruction"]` from the CLI positional argument. `Delphi` reads `state["instruction"]` and `state["current_mission_id"]` when composing its prompt (absorbs the old `agent-context-aware` fix).

**Laws of Physics:**
1. Law 1: fully `async`. `AriadneThread.available_missions()` must not block.
2. Law 4: always returns a valid `mission_id` (never raises). On LLM failure, fall back to `"explore"`.
3. DIP: imports only from `ariadne/core/` and `ariadne/models.py`.

**Required Context Pills**
- [Structured Output Pattern (VLM/LLM)](../context/structured-output-pattern.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Gemini Flash Default LLM](../context/gemini-flash-default.md)

### Acceptance criteria
1. `AriadneState` has `instruction: str`.
2. `Interpreter` actor resolves exact-mission fast path without an LLM call (unit test).
3. Unknown portal → `current_mission_id == "explore"` without raising.
4. `Delphi.__call__` prompt contains both `state["instruction"]` and `state["current_mission_id"]`.

### Test command
```bash
python -m pytest tests/unit/automation/ariadne/test_interpreter.py -q
```
