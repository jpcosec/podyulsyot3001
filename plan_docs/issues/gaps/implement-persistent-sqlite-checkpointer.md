# Implement: Persistent SQLite Checkpointer

**Explanation:** The orchestrator currently uses `MemorySaver`, which means all session state is lost if the process restarts. For reliable job applications and Human-In-The-Loop (HITL) support, we need a persistent database checkpointer.

**Reference:** 
- `src/automation/ariadne/graph/orchestrator.py`
- `langgraph.checkpoint.sqlite`

**What to fix:** Replace `MemorySaver` with `SqliteSaver` or `AsyncSqliteSaver`.

**How to do it:**
1.  Initialize a SQLite database at `data/ariadne/checkpoints.db`.
2.  Update the `create_ariadne_graph` factory to use the persistent checkpointer.
3.  Verify that a session can be resumed after a manual process kill.

**Depends on:** none
