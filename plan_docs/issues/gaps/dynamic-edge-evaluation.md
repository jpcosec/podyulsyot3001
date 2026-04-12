# Fix: Dynamic Edge Evaluation in Orchestrator

**Explanation:** The current `_find_safe_sequence` and edge selection logic in `orchestrator.py` picks the first edge matching the `from_state`. In portals like StepStone, a state can have multiple outgoing edges (e.g., onsite apply vs. external apply). Picking blindly leads to wrong navigation paths.

**Reference:**
- `src/automation/ariadne/graph/orchestrator.py`
- `src/automation/portals/stepstone/maps/easy_apply.json`

**What to fix:** The orchestrator must evaluate all outgoing edges and select the one whose target actually exists in the current browser snapshot.

**How to do it:**
1.  Update the edge selection logic to accept the current `dom_elements` list.
2.  Iterate through candidate edges and verify if the `AriadneTarget` (css/text) is present in the snapshot.
3.  Prioritize the edge that matches the current live UI.

**Depends on:** none
