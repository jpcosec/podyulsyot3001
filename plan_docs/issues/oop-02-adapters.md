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
- `src/automation/main.py::_check_browseros_running` -> move behavior into `src/automation/ariadne/core/adapters/browseros.py::BrowserOSAdapter/is_healthy` via `find_symbol(include_body=True)` + `replace_symbol_body`.
- `src/automation/main.py::_launch_browseros` -> move behavior into `src/automation/ariadne/core/adapters/browseros.py::BrowserOSAdapter/__aenter__`; keep spawned-process ownership on the adapter instance.
- `src/automation/main.py::_ensure_browseros` -> dissolve into `BrowserOSAdapter/__aenter__` and delete the legacy function after `find_referencing_symbols` confirms no callers remain.
- `src/automation/motors/browseros/executor.py::BrowserOSCliExecutor/take_snapshot` -> absorb into `src/automation/ariadne/core/adapters/browseros.py::BrowserOSAdapter/perceive`.
- `src/automation/motors/browseros/executor.py::BrowserOSCliExecutor/execute` -> absorb into `src/automation/ariadne/core/adapters/browseros.py::BrowserOSAdapter/act`.
- `src/automation/motors/crawl4ai/executor.py::Crawl4AIExecutor/__aenter__`, `__aexit__`, `take_snapshot`, `execute` -> absorb into `src/automation/ariadne/core/adapters/crawl4ai.py::Crawl4AIAdapter` methods with the same lifecycle ownership boundary.
- `src/automation/main.py::_get_executor` -> replace with adapter construction only; after adapter wiring lands, use `find_referencing_symbols` and remove executor-specific branching that survives only for legacy paths.

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
- [Peripheral Adapter Contract](../context/peripheral-adapter-contract.md)
- [Sensor Contract](../context/sensor-contract.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 2 (One Browser Per Mission):** A single `async with executor` block must wrap the entire graph execution. Nodes must never open or close the browser themselves.
