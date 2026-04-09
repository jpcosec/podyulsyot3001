# BrowserOS Chat Agent Surface Is Not Fully Validated For Runtime Use

**Explanation:** The repository now treats BrowserOS MCP as the canonical required runtime contract for scrape rescue, which is correct for the current architecture. However, the BrowserOS `/chat` agent surface is still present in the codebase and docs for other workflows, and it has not been fully validated as a dependable runtime surface for production use in this repo.

This matters because `/chat` may still be used for:
1. Level 2 trace capture
2. exploratory agent sessions
3. future apply/discovery workflows

But current repo confidence is weaker there than for MCP.

**Reference:**
- `src/automation/motors/browseros/agent/openbrowser.py`
- `src/automation/motors/browseros/agent/provider.py`
- `docs/reference/external_libs/browseros/live_agent_validation.md`
- `plan_docs/contracts/browseros_level2_trace.md`

**What to fix:** Validate and document the real runtime reliability envelope of BrowserOS `/chat` for the workflows that still depend on it, or explicitly narrow repo support if it is not stable enough. This parent issue is atomized into dependency inventory and runtime validation tasks.

**How to do it:**
1. Inventory `/chat` dependencies in `plan_docs/issues/gaps/browseros-chat-dependency-inventory-is-not-explicit.md`.
2. Validate runtime reliability in `plan_docs/issues/gaps/browseros-chat-runtime-reliability-is-not-validated.md`.
3. Update docs/contracts from the resulting evidence.

**Depends on:** `plan_docs/issues/gaps/browseros-chat-runtime-reliability-is-not-validated.md`
