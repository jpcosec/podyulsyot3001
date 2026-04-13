# Single Browser Session: Universal async with Wrapping

**Explanation:** Every graph execution must wrap the executor in `async with executor as active_executor` so Chromium opens once and stays alive for the full session. This is implemented in `run_scrape` but must be the universal pattern in the new CLI.

**Reference:** `src/automation/main.py` (`run_scrape:318-323`), `src/automation/motors/crawl4ai/executor.py`

**Status:** Partial — `run_scrape` does it correctly; `run_apply` does not. The new universal `run_ariadne` must inherit the correct pattern.

**Why it matters:** Without `async with executor`, `Crawl4AIExecutor.__aenter__` is never called, so there is no persistent Chromium process. Each `execute_deterministic` call would start/stop the browser, destroying SPA state (React/Vue memory, session cookies, open modals) between the `observe` and `execute` steps.

**Real fix:**
The new `run_ariadne()` in `main.py` must follow this pattern:
```python
async with executor as active_executor:
    config["configurable"]["executor"] = active_executor
    async with create_ariadne_graph() as app:
        async for chunk in app.astream(...):
            ...
```

**Don't:** Pass the uninitialized executor directly in `config["configurable"]["executor"]` outside the context manager.

**Steps:**
1. Implement `run_ariadne()` in the CLI rewrite (see `cli-rewrite.md`) with correct nesting.
2. Verify `Crawl4AIExecutor.__aexit__` calls `kill_session(self.session_id)` before closing the crawler.
3. Fitness test: assert `AsyncWebCrawler.__aenter__` is called exactly once per graph run (tracked in `test_single_browser_session.py`).
