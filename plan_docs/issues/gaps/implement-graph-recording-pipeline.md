# Implement: Graph Recording Pipeline

**Explanation:** In Ariadne 2.0, we must capture every node transition and agent action into a "Graph Trace" to enable map promotion (self-healing). Currently, the orchestrator executes but does not persist any audit trail or promotion candidates.

**Reference:** 
- `plan_docs/ariadne/recording_and_promotion.md`
- `src/automation/ariadne/graph/orchestrator.py`

**What to fix:** A capability that logs the sequence of `(State, Edge, Result)` into a JSONL trace file.

**How to do it:**
1.  Implement a `GraphRecorder` tool or node-wrapper.
2.  Capture the `AriadneState` snapshot and the chosen `AriadneEdge` at each iteration.
3.  Persist the trace to `data/ariadne/recordings/` using the `thread_id`.

**Depends on:** none
