# Fix: Atomic Micro-Batching with Failure Indexing

**Explanation:** Current micro-batching for Crawl4AI simply joins JavaScript fragments. If a middle action fails, the DOM is left partially mutated, but the orchestrator doesn't know where it stopped. This leads to a "Dirty DOM" state that confuses recovery agents.

**Reference:**
- `src/automation/ariadne/translators/crawl4ai.py`
- `src/automation/motors/crawl4ai/executor.py`

**What to fix:** Batch scripts must wrap each action in a try/catch block and return the index of the failed action.

**How to do it:**
1.  Update `Crawl4AITranslator` to generate a script that tracks the current action index.
2.  Wrap each intent's JS in a try/catch that returns `{"failed_at": index, "error": msg}`.
3.  Update `ExecutionResult` to include `completed_count` or `failed_at_index`.
4.  Update the orchestrator to resume from the last successful sub-step instead of aborting the whole batch.

**Depends on:** none
