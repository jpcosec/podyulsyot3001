# Zero-Shot Navigation: Typed MapNotFoundError and Explore Fallback Mission

**Umbrella:** depends on `ariadne-oop-skeleton.md` and `interpreter-node.md`.

**Explanation:** When Ariadne encounters a portal with no map, the system must distinguish a legitimate "no map exists" case from a real load error. `Labyrinth.load_from_db()` must raise a named `MapNotFoundError`, and the `Interpreter` actor must catch it narrowly and fall back to a `"explore"` mission.

**Reference:** `src/automation/ariadne/core/cognition.py` (`Labyrinth.load_from_db`), `src/automation/ariadne/core/actors.py` (`Interpreter`), `src/automation/ariadne/exceptions.py`

**Status:** Not started.

**Why it's wrong:** A bare `except Exception` in `parse_instruction_node` hides real bugs (permissions error, malformed JSON, import failures) and conflates them with the expected "portal not yet mapped" case. It also defaults to `available_missions[0]` arbitrarily instead of a named explore mission.

**Real fix:**
1. `Labyrinth.load_from_db(portal)` raises `MapNotFoundError(portal_name)` (defined in `exceptions.py`) when no map exists.
2. `Interpreter.__call__` catches only `MapNotFoundError` narrowly and sets `current_mission_id = "explore"`.
3. `"explore"` mission has no `AriadneThread` edges — `Theseus` detects this and delegates to `Delphi` immediately.
4. All other exceptions propagate normally.

**Don't:** Use `except Exception` as a map-missing catch-all.

### 📦 Required Context Pills
- [Error Contract](../context/error-contract.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Node Implementation Pattern](../context/node-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** Repository access must be `async`.
- **DIP Enforcement:** Domain errors must be defined in `ariadne/` and caught in `interpreter.py`.
