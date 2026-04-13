# Set-of-Mark: Inject Hints Before Agent Screenshot

**Explanation:** The LLM rescue agent must receive a screenshot with yellow `[AA]`/`[AB]` hint labels already painted on interactive elements — not a raw screenshot. `HintingTool.inject_hints()` must be called inside `observe_node` before the snapshot is stored.

**Reference:** `src/automation/ariadne/graph/orchestrator.py` (observe_node), `src/automation/ariadne/capabilities/hinting.js`

**Status:** Not started. `observe_node` takes raw snapshot without hint injection.

**Why it's wrong:** Without hints, the agent must guess CSS selectors or element positions from a raw screenshot. This causes hallucinations (wrong selectors), high token usage (full DOM tree instead of small hints dict), and fragile behavior across portals with dynamic class names.

**Real fix:**
1. After `take_snapshot()` in `observe_node`, call `HintingTool.inject_hints()` on the live page.
2. Store the resulting `{hint_id: description}` dict in `state["session_memory"]["hints"]`.
3. Re-capture screenshot after injection to get the annotated image.
4. Pass `hints` dict + annotated screenshot to the agent, not the raw DOM.
5. Restrict agent MCP tools to `click_hint(id)` and `fill_hint(id, value)` when hints are available.

**Don't:** Pass the full DOM tree to the agent as long as hints are available — it multiplies token cost by 20x.

**Steps:**
1. Add `HintingTool` invocation to `observe_node` after snapshot.
2. Store `hints_available: bool` and `hints: dict` in `session_memory`.
3. Update agent prompt builder to use hints dict when `hints_available` is True.
4. Test: assert agent prompt contains `[AA]` references when hints are injected.
