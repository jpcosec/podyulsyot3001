# Fix: test_sync_io_detector.py — Run Real Graph, Not Just take_snapshot()

**Explanation:** The `SyncIODetector` class is well-designed — it patches `builtins.open` and correctly skips boot-time I/O. But the test only calls `executor.take_snapshot()` inside the hot loop window, never the graph. If `observe_node` or `apply_local_heuristics` were doing a synchronous `open()` to reload a map mid-run, this test would never catch it.

**Reference:** `tests/architecture/test_sync_io_detector.py:62–77`

**Status:** False positive. The detector is correct; the execution scope is wrong.

**What is wrong:**
```python
# Current — only exercises the executor, not the graph nodes
async with executor:
    await executor.take_snapshot()  # graph nodes never run
```

The invariant is: *no graph node reads from disk synchronously during the hot loop.* The current test never enters the hot loop.

**Fix:**
Replace the body inside `detector.start()` / `detector.stop()` with a real multi-node graph run:

```python
@pytest.mark.asyncio
async def test_no_sync_io_in_hot_loop():
    """Fitness: no synchronous disk I/O during graph node execution."""
    repo = MapRepository()  # allowed — this is boot time

    detector = SyncIODetector()
    detector.start()  # hot loop begins here — open() is now tracked

    initial_state = {
        "instruction": "easy_apply",
        "portal_name": "fitness_test",
        "job_id": "fitness-sync-io-test",
        "portal_mode": "fitness_test",
        "current_url": "https://example.com",
        "current_state_id": "start",
        "dom_elements": [],
        "screenshot_b64": None,
        "profile_data": {},
        "job_data": {},
        "session_memory": {},
        "errors": [],
        "history": [],
        "patched_components": {},
        "path_id": None,
        "current_mission_id": "easy_apply",
    }

    try:
        executor = Crawl4AIExecutor()
        config = {
            "configurable": {
                "thread_id": "fitness-sync-io-test",
                "motor_name": "crawl4ai",
                "record_graph": False,
            }
        }
        async with executor as active_executor:
            config["configurable"]["executor"] = active_executor
            async with create_ariadne_graph(use_memory=False) as app:
                async for _ in app.astream(initial_state, config):
                    pass  # run through observe → exec → heuristics → agent → HITL

        if detector.hot_loop_calls:
            files = [c["file"] for c in detector.hot_loop_calls[:3]]
            pytest.fail(
                f"Sync I/O detected in hot loop: {len(detector.hot_loop_calls)} reads. "
                f"Files: {files}"
            )
    finally:
        detector.stop()
```

**Note on `SyncIODetector`:** The class itself is correct and should not be changed. Only the test body needs updating.

**Requires:** `fitness_test` portal map. `GOOGLE_API_KEY` must be set.

**Don't:** Add any `open()` call suppression inside the detector — it must catch real violations. If the test fails because `observe_node` calls `get_map_async()` synchronously somewhere, that is a real bug to fix.

**Steps:**
1. Add `from src.automation.ariadne.graph.orchestrator import create_ariadne_graph` import.
2. Replace test body with implementation above (keep `SyncIODetector` class unchanged).
3. Run: `python -m pytest tests/architecture/test_sync_io_detector.py -v -s`
4. If it fails, trace the `stack` in `detector.hot_loop_calls` to find the offending `open()` call and fix at source.

### 📦 Required Context Pills
- [Law 1 — No Blocking I/O](../context/law-1-async.md)
- [Node Implementation Pattern](../context/node-pattern.md)
- [Async Test Pattern (LangGraph)](../context/async-test-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All disk, network, and subprocess calls MUST use `async/await`. Verify by running the sync I/O detector. No `open()`, `time.sleep()`, or `requests`.
- **DIP Enforcement:** Domain layers (`ariadne`) MUST NOT import from infrastructure layers (`motors`). Use `config["configurable"]["executor"]`.
