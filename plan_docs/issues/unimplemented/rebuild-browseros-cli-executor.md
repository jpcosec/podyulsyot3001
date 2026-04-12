# Rebuild: BrowserOS CLI Executor

**Explanation:** The legacy BrowserOS motor was purged in Epic 0. We need to rebuild it as a "Dumb Executor" that satisfies the new `Executor` protocol and accepts atomic `BrowserOSCommand` JIT instructions.

**Reference:** 
- `plan_docs/ariadne/execution_interfaces.md`
- `src/automation/motors/browseros/executor.py` (To be created)

**What to fix:** A JIT-compliant BrowserOS executor that performs MCP tool calls without any planning logic.

**How to do it:**
1.  Implement the `BrowserOSCliExecutor` class.
2.  Implement the `execute` method to handle `click`, `fill`, `upload`, and `press` tools.
3.  Ensure it uses the BrowserOS MCP port (9000) directly.
4.  Remove all legacy "Playbook" or "Replay" logic.

**Depends on:** `plan_docs/issues/unimplemented/segregated-motor-protocols.md`
