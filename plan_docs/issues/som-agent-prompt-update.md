# Set-of-Mark: Delphi Prompt and Hint Consumption

**Umbrella:** depends on `ariadne-oop-skeleton.md`, `som-hint-injection.md`.

**Explanation:** `Delphi` must consume the hints dictionary and the annotated screenshot produced by `Theseus`/`Sensor` and reference elements via their `[AA]` labels.

**Reference:** `src/automation/ariadne/core/actors.py` (`Delphi`)

**Status:** Not started.

### 📦 Required Context Pills
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 4 - Finite Routing](../context/law-4-finite-routing.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Node Implementation Pattern](../context/node-pattern.md)
- [Set-of-Mark (SoM) Pattern](../context/som-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.
