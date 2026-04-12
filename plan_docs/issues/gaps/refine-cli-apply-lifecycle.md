# Refine: CLI Apply Lifecycle

**Explanation:** The CLI entry point in `src/automation/main.py` is a skeleton. To provide a production-grade experience, it must handle the full LangGraph lifecycle: starting a new thread, streaming real-time node updates, persisting state artifacts (like screenshots), and managing Human-In-The-Loop interrupts via the TUI/terminal.

**Reference:** 
- `src/automation/main.py`
- `src/automation/ariadne/graph/orchestrator.py`

**What to fix:** A functional `apply` command that manages the end-to-end user experience of a job application.

**How to do it:**
1.  Update the `apply` subcommand to support session initialization (loading profile, setting up thread ID).
2.  Implement a robust streaming loop that prints node transitions and highlights errors.
3.  Handle `interrupt_before` breakpoints: detect when the graph is paused at HITL, notify the user, and provide instructions for resuming.
4.  Persist the final `ExecutionResult` and any artifacts (trace, screenshots) to the `data/jobs/` directory.

**Depends on:** none
