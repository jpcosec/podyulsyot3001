# Zero-Shot Navigation: Typed MapNotFoundError and Explore Fallback Mission

**Explanation:** When Ariadne encounters a portal with no map, the system must distinguish a legitimate "no map exists" case from a real load error. The interpreter node must handle this with a named `MapNotFoundError` and fall back to a generic `"explore"` mission.

**Reference:** `src/automation/ariadne/repository.py`, `src/automation/ariadne/graph/nodes/interpreter.py` (to be created)

**Status:** Not started. `MapRepository.get_map()` raises `FileNotFoundError` which is caught broadly in `interpreter.py` snippets using bare `except Exception`.

**Why it's wrong:** A bare `except Exception` in `parse_instruction_node` hides real bugs (permissions error, malformed JSON, import failures) and conflates them with the expected "portal not yet mapped" case. It also defaults to `available_missions[0]` arbitrarily instead of a named explore mission.

**Real fix:**
1. In `MapRepository.get_map()`, raise `MapNotFoundError(portal_name)` (custom exception) when the map file doesn't exist.
2. In `parse_instruction_node`, catch only `MapNotFoundError` narrowly and set `current_mission_id = "explore"`.
3. The `"explore"` mission has no deterministic edges — it signals to `execute_deterministic` to skip directly to heuristics/agent.
4. All other exceptions propagate normally.

**Don't:** Use `except Exception` as a map-missing catch-all.

### 📦 Required Context Pills
- [Error Contract](../context/error-contract.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Node Implementation Pattern](../context/node-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** Repository access must be `async`.
- **DIP Enforcement:** Domain errors must be defined in `ariadne/` and caught in `interpreter.py`.
