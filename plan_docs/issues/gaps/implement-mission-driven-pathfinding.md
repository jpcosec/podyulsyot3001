# Implement: Mission-Driven Pathfinding

**Explanation:** The `execute_deterministic_node` currently picks the first matching edge from the `current_state_id`. If a portal map contains multiple flows (e.g., "Apply" and "Skip"), the orchestrator might take the wrong path. We need to implement **Mission Filtering** using a `task_id` or `mission_goal` stored in the state.

**Reference:** 
- `src/automation/ariadne/graph/orchestrator.py`
- `src/automation/ariadne/models.py` (AriadneMap)

**What to fix:** Navigation logic that only selects edges belonging to the current mission.

**How to do it:**
1.  Update `AriadneEdge` to include an optional `mission_id` (e.g. 'onsite_apply').
2.  Add `current_mission_id` to the `AriadneState`.
3.  Update the edge selection loop in `execute_deterministic_node` to filter by `mission_id`.
4.  Update the CLI to allow specifying the mission.

**Depends on:** none
