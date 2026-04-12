# Fix: MapRepository Async/Await Bug in Orchestrator

**Explanation:** The orchestrator calls `MapRepository.get_map_async()` but doesn't await it properly, causing "coroutine was never awaited" warnings. When called from sync context, should use sync version or ensure proper async handling.

**Reference:** `src/automation/ariadne/graph/orchestrator.py` - lines 391, 498

**What to fix:** Ensure proper async handling or use sync fallback in observe_node

**Depends on:** none