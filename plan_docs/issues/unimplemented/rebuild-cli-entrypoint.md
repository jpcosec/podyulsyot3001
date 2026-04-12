# Rebuild: CLI Entrypoint for Ariadne 2.0

**Explanation:** The `src/automation/main.py` is currently a stub. We need to rebuild it to invoke the new LangGraph orchestrator instead of the deleted `AriadneSession`.

**Reference:** 
- `src/automation/main.py`
- `src/automation/ariadne/graph/orchestrator.py`

**What to fix:** A functional CLI that can launch `scrape` and `apply` using the Ariadne 2.0 graph.

**How to do it:**
1.  Restore the argument parsing logic for `apply` and `scrape`.
2.  Implement the runner that initializes the `AriadneState` and calls `graph.ainvoke()`.
3.  Ensure the CLI handles LangGraph's streaming output and HITL interrupts correctly.

**Depends on:** `plan_docs/issues/unimplemented/langgraph-stategraph-controller.md`
