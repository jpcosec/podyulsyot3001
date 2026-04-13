# Hint Injection Failure Fallback: Raw DOM + Coordinate Mode

**Explanation:** When `HintingTool` cannot inject hints (CSP, closed Shadow DOM, Canvas-rendered page), the agent must degrade gracefully to a raw screenshot + simplified DOM tree, and ultimately to coordinate-based clicks.

**Reference:** `src/automation/ariadne/capabilities/hinting.js`, `src/automation/ariadne/models.py` (`AriadneTarget.vision`)

**Status:** Not started. `AriadneTarget` has a `vision` field but nothing populates it or routes to coordinate-based clicking.

**Why it's missing:** Without this fallback, a single portal with a strict CSP causes the entire rescue cascade to stall — no hints means no agent actions, which triggers circuit breaker, which escalates to HITL unnecessarily.

**Real fix:**
1. `observe_node` detects hint injection failure and sets `session_memory["hints_available"] = False`.
2. Agent checks `hints_available`:
   - `True` → use hints dict + annotated screenshot (cheap, accurate).
   - `False, DOM available` → use simplified DOM tree + raw screenshot (expensive, fuzzy text match).
   - `False, DOM unusable` → ask VLM for `(x, y)` coordinates of target element, populate `AriadneTarget.vision`, execute `click_coords(x, y)` MCP tool.
3. Add `click_coords(x: int, y: int)` as an MCP tool wrapper in the agent's tool set.

**Don't:** Default to DOM-tree mode when hints are available — it's 20x more expensive per agent invocation.

**Steps:**
1. Add hint injection error handling in `observe_node`, set `session_memory["hints_available"]`.
2. Implement agent prompt switching logic based on `hints_available`.
3. Add `click_coords` MCP tool invocation path.
4. Test: simulate CSP block, assert agent switches to DOM mode without crashing.
