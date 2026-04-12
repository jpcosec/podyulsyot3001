# Fix: Async-Safe Mode Config Loading

**Explanation:** `JsonConfigMode` currently performs synchronous `open().read()` calls inside its `__init__` method. Since this is called within the LangGraph hot loop, it blocks the asyncio event loop, severely degrading performance under concurrency.

**Reference:**
- `src/automation/ariadne/modes/portals.py`
- `src/automation/ariadne/modes/registry.py`

**What to fix:** Move config loading to an asynchronous, lazy-loading pattern or pre-load all configs at boot time.

**How to do it:**
1.  Implement a class-level cache for configurations in `JsonConfigMode`.
2.  Pre-load the `configs/` directory into a shared memory registry at system startup.
3.  Ensure `ModeRegistry` returns instances that already have their data populated, avoiding I/O during graph execution.

**Depends on:** none
