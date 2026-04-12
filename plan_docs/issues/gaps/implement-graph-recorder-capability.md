# Implement: Graph Recorder Capability

**Explanation:** In Ariadne 2.0, we must capture every node transition and agent action into a "Graph Trace" to enable map promotion. Currently, the orchestrator executes but does not persist any audit trail or promotion candidates. This fulfills the "Recording" stage of the Master Doc.

**Reference:** 
- `plan_docs/ariadne/recording_and_promotion.md`
- `src/automation/ariadne/graph/orchestrator.py`

**What to fix:** A capability tool that logs the sequence of `(State, Edge, Result)` into a JSONL trace file.

**How to do it:**
1.  Implement a `GraphRecorder` capability.
2.  Add a hook in the `StateGraph` (or a dedicated node) to capture the state snapshot and chosen edge at each step.
3.  Persist the trace to `data/ariadne/recordings/` using the `thread_id`.

**Depends on:** `plan_docs/issues/gaps/implement-persistent-sqlite-checkpointer.md`
