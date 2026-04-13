# Theseus: Adapter Health Guard Before Every Action

**Umbrella:** depends on `oop-02-adapters.md` and `oop-04-theseus.md`.

### 1. Explanation
 Before any perception or motor call, `Theseus` must verify the browser adapter is alive via `BrowserAdapter.is_healthy()`. If the physical layer is down (BrowserOS MCP unreachable, Crawl4AI crawler closed, process killed mid-mission), the fast path must fail immediately with a clean fatal error instead of spending LLM tokens, freezing the graph, or producing undefined hangs.

### 2. Reference
 `plan_docs/design/browseros-adapter-lifecycle.md` ("Proposed Theseus responsibility"), `src/automation/ariadne/core/actors.py` (`Theseus`), `src/automation/ariadne/core/periphery.py` (`BrowserAdapter.is_healthy`), `src/automation/ariadne/core/adapters/browseros.py`

**Why it matters:**
- BrowserOS can crash mid-mission (AppImage segfault, OS OOM, user closes window). Without a health guard, `Sensor.perceive()` would hang or return garbage and `Delphi` would be invoked on a dead browser, burning tokens for nothing.
- The adapter is the only place that knows how to answer "am I alive?" — `Theseus` must not duplicate health logic; it must ask the adapter.
- This is a just-in-time guard, not a startup check. Startup health is `BrowserAdapter.__aenter__`'s job; this issue covers the steady-state loop.

### 3. Real fix

1. `Theseus.__call__` step 1 (before `Sensor.perceive()`):
   ```python
   if not await self.sensor.is_healthy():
       return {"errors": ["FatalError: browser adapter unhealthy mid-mission"]}
   ```
2. Graph routing: any `FatalError` in `state["errors"]` short-circuits to terminal state (no Delphi retry, no cascade). This is distinct from `danger_type = "http_error"` which escalates to HITL — a dead adapter cannot be rescued by a human clicking around.
3. `BrowserOSAdapter.is_healthy()` polls `GET {base_url}/mcp` with a 2s timeout and returns `False` on any network error or non-200. `Crawl4AIAdapter.is_healthy()` checks the underlying `AsyncWebCrawler` is open.
4. `is_healthy()` must be cheap. No retries, no backoff — one shot, then return. Retries are the orchestrator's concern, not the health check's.

**Don't:**
- Don't call `is_healthy()` from inside `Delphi` — by the time Delphi runs, Theseus has already gated.
- Don't couple the health check to a specific portal or mission. It's a physical-layer concern.
- Don't raise; return the error in `state["errors"]` so the graph routes cleanly.

### 📦 Required Context Pills
- [Error Contract](../context/error-contract.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Peripheral Adapter Contract](../context/peripheral-adapter-contract.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
