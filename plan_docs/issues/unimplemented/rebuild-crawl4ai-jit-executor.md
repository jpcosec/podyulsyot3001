# Rebuild: Crawl4AI JIT Executor

**Explanation:** The legacy Crawl4AI apply engine was purged. We need to rebuild it as a JIT Executor that accepts `CrawlCommand` (multi-line C4A-Scripts) and satisfies the new `Executor` protocol.

**Reference:** 
- `plan_docs/ariadne/execution_interfaces.md`
- `src/automation/motors/crawl4ai/executor.py` (To be created)

**What to fix:** A JIT-compliant Crawl4AI executor that can execute atomic or batched C4A-Scripts.

**How to do it:**
1.  Implement the `Crawl4AIExecutor` class.
2.  Implement the `execute` method to run `CrawlCommand` scripts using the Crawl4AI `arun()` interface.
3.  Implement support for Playwright hooks (e.g. file upload) as defined in the `CrawlCommand`.

**Depends on:** `plan_docs/issues/unimplemented/segregated-motor-protocols.md`
