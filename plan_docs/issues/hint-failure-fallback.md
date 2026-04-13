# Hint Injection Failure Fallback: Raw DOM + Coordinate Mode

**Umbrella:** depends on `ariadne-oop-skeleton.md`, `som-hint-injection.md`.

**Explanation:** When the `HintingCapability` cannot inject hints (CSP, closed Shadow DOM, Canvas-rendered page), `Delphi` must degrade gracefully: raw screenshot + simplified DOM tree first, then coordinate-based clicks.

**Reference:** `src/automation/ariadne/capabilities/hinting.js`, `src/automation/ariadne/core/actors.py` (`Theseus`, `Delphi`), `src/automation/ariadne/models.py` (`AriadneTarget.vision`)

**Status:** Not started. `AriadneTarget` has a `vision` field but nothing populates it or routes to coordinate-based clicking.

**Why it's missing:** Without this fallback, a single portal with a strict CSP causes the entire rescue cascade to stall — no hints means no agent actions, which triggers circuit breaker, which escalates to HITL unnecessarily.

**Real fix:**
1. `Theseus` detects hint injection failure and sets `session_memory["hints_available"] = False`.
2. `Delphi` checks `hints_available`:
   - `True` → use hints dict + annotated screenshot (cheap, accurate).
   - `False, DOM available` → use simplified DOM tree + raw screenshot (expensive, fuzzy text match).
   - `False, DOM unusable` → ask VLM for `(x, y)` coordinates, populate `AriadneTarget.vision`, emit `click_coords(x, y)` through `Motor.act()`.
3. Add `click_coords(x: int, y: int)` as a `MotorCommand` variant.

**Don't:** Default to DOM-tree mode when hints are available — it's 20x more expensive per agent invocation.

**Steps:**
1. Add hint injection error handling in `observe_node`, set `session_memory["hints_available"]`.
2. Implement agent prompt switching logic based on `hints_available`.
3. Add `click_coords` MCP tool invocation path.
4. Test: simulate CSP block, assert agent switches to DOM mode without crashing.
