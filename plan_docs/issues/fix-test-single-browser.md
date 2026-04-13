# Fix: test_single_browser.py — Run Real Graph, Not Just take_snapshot()

**Explanation:** The test spies on `Crawl4AIExecutor.__aenter__`/`__aexit__` correctly, but only calls `executor.take_snapshot()` inside the context — never the LangGraph orchestrator. If the orchestrator were to recreate the browser between nodes, this test would not catch it.

**Reference:** `tests/architecture/test_single_browser.py:33–43`

**Status:** False positive. The spy mechanics are correct; the execution scope is wrong.

**What is wrong:**
```python
# Current — only tests the executor in isolation
async with executor:
    await executor.take_snapshot()  # LangGraph never runs
```

The invariant being tested is: *the orchestrator opens the browser once across a multi-node graph run.* The current test never invokes the orchestrator.

**Fix:**
Replace the body of the `async with executor` block with a real graph run using the `fitness_test` portal (targets that always fail, forcing multi-node traversal):

```python
@pytest.mark.asyncio
async def test_executor_maintains_single_browser_session():
    """Fitness: browser opens once and closes once across a full graph run."""
    enter_count = 0
    exit_count = 0

    original_aenter = Crawl4AIExecutor.__aenter__
    original_aexit = Crawl4AIExecutor.__aexit__

    async def tracked_aenter(self):
        nonlocal enter_count
        enter_count += 1
        return await original_aenter(self)

    async def tracked_aexit(self, *args):
        nonlocal exit_count
        exit_count += 1
        return await original_aexit(self, *args)

    initial_state = {
        "instruction": "easy_apply",
        "portal_name": "fitness_test",
        "job_id": "fitness-browser-test",
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

    with patch.object(Crawl4AIExecutor, "__aenter__", tracked_aenter):
        with patch.object(Crawl4AIExecutor, "__aexit__", tracked_aexit):
            executor = Crawl4AIExecutor()
            config = {
                "configurable": {
                    "thread_id": "fitness-browser-test",
                    "motor_name": "crawl4ai",
                    "record_graph": False,
                }
            }
            async with executor as active_executor:
                config["configurable"]["executor"] = active_executor
                async with create_ariadne_graph(use_memory=False) as app:
                    async for _ in app.astream(initial_state, config):
                        pass  # let the graph run to HITL

    assert enter_count == 1, f"Browser opened {enter_count} times — singleton violated"
    assert exit_count == 1, f"Browser closed {exit_count} times — singleton violated"
```

**Requires:** `fitness_test` portal map with states targeting non-existent elements (so the cascade runs through multiple nodes before hitting HITL). `GOOGLE_API_KEY` must be set — the LLM rescue node will be invoked for real.

**Don't:** Mock `take_snapshot()` or any node inside the graph — the whole point is to observe the orchestrator's behavior.

**Steps:**
1. Add `from src.automation.ariadne.graph.orchestrator import create_ariadne_graph` import.
2. Replace the test body with the implementation above.
3. Verify a `fitness_test` portal map exists (or create a minimal one targeting `#does-not-exist`).
4. Run: `python -m pytest tests/architecture/test_single_browser.py -v -s`
5. Confirm `enter_count == 1` in output.
