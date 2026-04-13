# OOP 02 — Concrete BrowserAdapters (BrowserOS + Crawl4AI)

**Umbrella:** `ariadne-oop-skeleton.md`. Depends on `oop-01-scaffold.md`. Parallel with `oop-03-cognition.md`.

### 1. Explanation
Implement the two concrete `BrowserAdapter` subclasses and absorb all lifecycle logic currently held by `src/automation/main.py` and the existing executors. After this issue, `main.py` no longer launches BrowserOS or polls `/mcp`.

### 2. Reference
`plan_docs/design/browseros-adapter-lifecycle.md`, `src/automation/main.py` (BrowserOS startup block), `src/automation/motors/crawl4ai/executor.py`, `src/automation/motors/browseros/` (if present)

### 3. Real fix
Concrete `BrowserOSAdapter` and `Crawl4AIAdapter` implementing `BrowserAdapter`.

### 4. Steps
1. `core/adapters/browseros.py` — `BrowserOSAdapter(BrowserAdapter)`
   - `__init__(base_url, appimage_path)`.
   - `is_healthy()` — async GET `/mcp` with 2s timeout.
   - `__aenter__` — if unhealthy and `appimage_path` set, spawn process, poll up to 30s, then raise `TimeoutError`.
   - `__aexit__` — terminate spawned process (only if we spawned it).
   - `perceive()` and `act()` — wrap MCP calls.
2. `core/adapters/crawl4ai.py` — `Crawl4AIAdapter(BrowserAdapter)`
   - Wrap `AsyncWebCrawler` so `__aenter__`/`__aexit__` own the Chromium lifecycle (Law 2).
   - `is_healthy()` — trivial True when `_crawler` is open.
   - `perceive()` / `act()` — delegate to the underlying crawler.
3. Delete from `main.py`: `_ensure_browseros`, AppImage launch, `/mcp` polling, dead block at lines 382–396. `main.py` now only instantiates the adapter and `async with adapter:`.
4. Law 1: all methods `async`; the `/mcp` poll uses `asyncio.to_thread(requests.get, ...)` or `httpx.AsyncClient`.

### 4.1 Serena AST refactor operations
*Note from Context Compiler: `main.py` has already been refactored in `ee0c1d0` and `f1df743` and NO LONGER contains the `_ensure_browseros` or legacy `/mcp` polling logic. The executor's job is to ensure `core/adapters/browseros.py` and `core/adapters/crawl4ai.py` conform to `BrowserAdapter` and are wired correctly.*

- Review the already scaffolded `BrowserOSAdapter` in `src/automation/ariadne/core/adapters/browseros.py` to ensure it absorbs `take_snapshot` and `execute` correctly as `perceive` and `act`.
- Review the already scaffolded `Crawl4AIAdapter` in `src/automation/ariadne/core/adapters/crawl4ai.py` to ensure it conforms.
- Check `main.py` one last time to ensure `MotorRegistry` successfully resolves the adapter and correctly passes it into the `_build_config` logic.

### 5. Test command
1. `async with BrowserOSAdapter(...)` launches, waits for health, and cleans up the subprocess it owns.
2. `async with Crawl4AIAdapter(...)` opens Chromium exactly once per mission (regression test asserting `__aenter__` called once).
3. `main.py` contains zero BrowserOS/AppImage/MCP polling logic.
4. `python -m pytest tests/unit/automation/ tests/architecture/ -q` green.

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 2 - One Browser Per Mission](../context/law-2-single-browser.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Motor Contract](../context/motor-contract.md)
- [Browser Adapter Contract](../context/browser-adapter-contract.md)
- [Sensor Contract](../context/sensor-contract.md)

### 🚫 Non-Negotiable Constraints
- **Context Clarification (BrowserAdapter):** `src/automation/ariadne/contracts/base.py` currently defines `PeripheralAdapter`, but `src/automation/ariadne/core/periphery.py` defines `BrowserAdapter`. **You MUST implement `BrowserAdapter`** as specified in `core/periphery.py`. `base.py` is stale and will be cleaned up in `oop-08-cleanup.md`. Do not import `PeripheralAdapter`.
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 2 (One Browser Per Mission):** A single `async with adapter` block must wrap the entire graph execution. Nodes must never open or close the browser themselves.
