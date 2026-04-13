# Hint Injection Failure Fallback: Raw DOM + Coordinate Mode

**Umbrella:** depends on `ariadne-oop-skeleton.md`, `som-hint-injection.md`.

### 1. Explanation
 When the `HintingCapability` cannot inject hints (CSP, closed Shadow DOM, Canvas-rendered page), `Delphi` must degrade gracefully: raw screenshot + simplified DOM tree first, then coordinate-based clicks.

### 2. Reference
 `src/automation/ariadne/capabilities/hinting.js`, `src/automation/ariadne/core/actors.py` (`Theseus`, `Delphi`), `src/automation/ariadne/models.py` (`AriadneTarget.vision`)

**Status:** Not started. `AriadneTarget` has a `vision` field but nothing populates it or routes to coordinate-based clicking.

**Why it's missing:** Without this fallback, a single portal with a strict CSP causes the entire rescue cascade to stall — no hints means no agent actions, which triggers circuit breaker, which escalates to HITL unnecessarily.

### 3. Real fix

1. `Theseus` detects hint injection failure and sets `session_memory["hints_available"] = False`.
2. `Delphi` checks `hints_available`:
   - `True` → use hints dict + annotated screenshot (cheap, accurate).
   - `False, DOM available` → use simplified DOM tree + raw screenshot (expensive, fuzzy text match).
   - `False, DOM unusable` → ask VLM for `(x, y)` coordinates, populate `AriadneTarget.vision`, emit `click_coords(x, y)` through `Motor.act()`.
3. Add `click_coords(x: int, y: int)` as a `MotorCommand` variant.

**Don't:** Default to DOM-tree mode when hints are available — it's 20x more expensive per agent invocation.

### 4. Steps

1. Add hint injection error handling in `observe_node`, set `session_memory["hints_available"]`.
2. Implement agent prompt switching logic based on `hints_available`.
3. Add `click_coords` MCP tool invocation path.
4. Test: simulate CSP block, assert agent switches to DOM mode without crashing.

### 5. Test command
Simulate CSP block and assert agent switches to DOM mode.

### 📦 Required Context Pills
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 4 - Finite Routing](../context/law-4-finite-routing.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Node Implementation Pattern](../context/node-pattern.md)
- [Set-of-Mark (SoM) Pattern](../context/som-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.
