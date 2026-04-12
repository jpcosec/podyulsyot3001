# Implement: State Identification in Observe Node

**Explanation:** The `observe_node` currently fetches browser data but does not perform **State Identification**. To navigate correctly, Ariadne must know which semantic node it is currently on. It needs to match the live snapshot against the map's `presence_predicate` and detect any "Dangers" (security blocks) to trigger the fallback cascade.

**Reference:** 
- `src/automation/ariadne/graph/orchestrator.py`
- `src/automation/ariadne/models.py` (AriadneObserve)

**What to fix:** Functional state identification logic that updates `current_state_id` and detects blockers.

**How to do it:**
1.  Load the `AriadneMap` in `observe_node`.
2.  Iterate through all `states` in the map and evaluate their `presence_predicate` against the current URL and DOM.
3.  If a match is found, update `state['current_state_id']`.
4.  Call `portal_mode.inspect_danger(snapshot)` to check for CAPTCHAs.
5.  Update `session_memory['danger_detected']` or `session_memory['goal_achieved']` based on findings.

**Depends on:** none
