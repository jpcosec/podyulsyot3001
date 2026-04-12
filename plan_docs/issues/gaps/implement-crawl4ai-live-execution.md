# Implement: Crawl4AI Live Execution

**Explanation:** The `Crawl4AIExecutor` in `src/automation/motors/crawl4ai/executor.py` is currently a stub that mocks success and only prints the C4A-Script. To enable real browser interaction, it must instantiate the `AsyncWebCrawler` and use its `arun()` method to execute the JIT scripts.

**Reference:** 
- `src/automation/motors/crawl4ai/executor.py`
- `docs/standards/code/crawl4ai_usage.md` (Legacy reference for usage patterns)

**What to fix:** A functional `Crawl4AIExecutor` that performs real headless browser actions.

**How to do it:**
1.  Import `AsyncWebCrawler` and `CrawlerRunConfig` from `crawl4ai`.
2.  Implement the `execute` method to pass the `c4a_script` to `arun()`.
3.  Handle the `CrawlResult` and map it back to `ExecutionResult` (success/failed).
4.  Implement `take_snapshot` using Crawl4AI's HTML/Accessibility Tree extraction.

**Depends on:** none
