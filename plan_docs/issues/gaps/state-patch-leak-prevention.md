# Fix: State Patch Leak Prevention

**Explanation:** `patched_components` uses an `operator.ior` (dictionary merge) reducer. This causes patches applied in one state (e.g., Login) to persist in memory forever. If a future state has a component with the same name, it will use the stale patch, leading to "ghost clicks" on non-existent elements.

**Reference:**
- `src/automation/ariadne/models.py`
- `src/automation/ariadne/graph/orchestrator.py`

**What to fix:** Scoping patches to the state they were intended for, or ensuring the reducer is cleared on successful state transitions.

**How to do it:**
1.  Option A: Change `patched_components` key to a tuple/string of `state_id:component_name`.
2.  Option B: Update the `AriadneState` reducers to allow clearing the patch dictionary when the `current_state_id` changes.
3.  Update `_resolve_target` to look up patches using the new scoped keys.

**Depends on:** none
