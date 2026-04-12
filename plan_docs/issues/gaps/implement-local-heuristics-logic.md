# Implement: Local Heuristics Logic

**Explanation:** The `apply_local_heuristics_node` in `orchestrator.py` is currently a stub. To enable high-speed, cost-optimized recovery, it must invoke the active `PortalMode` from the `ModeRegistry` to apply contextual rules (patching selectors, normalizing text) before falling back to an expensive LLM call.

**Reference:** 
- `src/automation/ariadne/graph/orchestrator.py`
- `src/automation/ariadne/modes/registry.py`

**What to fix:** Functional logic in the heuristics node that retrieves the portal mode and calls `apply_local_heuristics`.

**How to do it:**
1.  Initialize the `ModeRegistry` within the node.
2.  Get the `portal_mode` ID from the state.
3.  Instantiate the mode and call its heuristics methods.
4.  Update the state with the patched components and clear the current error if a patch was successful.

**Depends on:** `plan_docs/issues/gaps/implement-deterministic-dispatch-logic.md`
