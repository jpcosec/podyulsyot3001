# BrowserOS Adapter Lifecycle

This design note captures the lifecycle responsibilities of the BrowserOS adapter and the expectation that runtime health checks belong to the physical adapter layer, not the CLI.

## Port map (source: `config.sample.json` in browseros-ai/BrowserOS repo)

```json
{
  "ports": {
    "cdp":       9000,
    "http_mcp":  9100,
    "agent":     9200,
    "extension": 9300
  }
}
```

| Port | Protocol | Used by |
|------|----------|---------|
| 9000 | CDP (WebSocket) | **Crawl4AI** connects here via `BrowserConfig(cdp_url="ws://localhost:9000")` — Sensor + Motor |
| 9100 | HTTP/SSE MCP | **Delphi** connects here for visual LLM reasoning (cold path) |
| 9200 | Agent API | BrowserOS native agent — autonomous navigation, passive session recording |
| 9300 | Extension | Chromium extension internal channel |

## Crawl4AI ↔ BrowserOS wiring

Crawl4AI does **not** launch its own browser. Instead it connects to BrowserOS's Chromium via CDP:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(cdp_url="ws://localhost:9000")

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url, config=run_config)
```

This means BrowserOS is the one and only Chromium instance. All Crawl4AI operations (fast-path scripts, extraction, screenshots) go through that shared browser. No Docker needed on our side.

## Health check

`is_healthy()` hits the MCP HTTP endpoint (port 9100), not the CDP port, because CDP is a WebSocket and doesn't respond to plain HTTP:

```python
async def is_healthy(self) -> bool:
    resp = await asyncio.to_thread(requests.get, "http://localhost:9100/health", timeout=2)
    return resp.status_code == 200
```

## Core idea

The logic for launching BrowserOS, polling health, and validating the runtime should live inside the BrowserOS adapter itself. Keeping that logic in `main.py` is a lifecycle anti-pattern because it mixes CLI orchestration with physical adapter concerns.

## Proposed `BrowserOSAdapter`

```python
import asyncio
import subprocess
import requests
from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig
from src.automation.ariadne.contracts.base import SnapshotResult, ExecutionResult, MotorCommand

CDP_URL  = "ws://localhost:9000"
MCP_URL  = "http://localhost:9100"

class BrowserOSAdapter:
    """Implementa Sensor y Motor apoyándose en Crawl4AI conectado al Chromium de BrowserOS."""

    def __init__(self, appimage_path: Optional[str] = None):
        self.appimage_path = appimage_path
        self._process: Optional[subprocess.Popen] = None
        self._crawler: Optional[AsyncWebCrawler] = None

    async def is_healthy(self) -> bool:
        """Verifica que BrowserOS esté respondiendo en el puerto MCP (9100)."""
        try:
            resp = await asyncio.to_thread(requests.get, f"{MCP_URL}/health", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    async def __aenter__(self) -> "BrowserOSAdapter":
        """Asegura que BrowserOS esté arriba y conecta Crawl4AI a su Chromium."""
        if not await self.is_healthy():
            if not self.appimage_path:
                raise RuntimeError(f"BrowserOS no responde en {MCP_URL} y no hay AppImage para levantarlo.")

            print(f"[⚙️] Levantando BrowserOS desde {self.appimage_path}...")
            self._process = subprocess.Popen(
                [self.appimage_path, "--no-sandbox"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            for _ in range(30):
                await asyncio.sleep(1)
                if await self.is_healthy():
                    print("[✅] BrowserOS listo.")
                    break
            else:
                self._kill_process()
                raise TimeoutError("BrowserOS falló al iniciar después de 30 segundos.")

        # Crawl4AI se conecta al Chromium de BrowserOS — no lanza browser propio
        browser_config = BrowserConfig(cdp_url=CDP_URL)
        self._crawler = AsyncWebCrawler(config=browser_config)
        await self._crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._crawler:
            await self._crawler.__aexit__(exc_type, exc_val, exc_tb)

    def _kill_process(self):
        if self._process:
            self._process.kill()
            self._process = None

    async def perceive(self) -> SnapshotResult:
        ...

    async def act(self, command: MotorCommand) -> ExecutionResult:
        ...
```

## Proposed `Theseus` responsibility

Before acting, `Theseus` should confirm the adapter is still healthy. If the physical layer is down, the fast path should fail immediately and let the graph surface a clean fatal error instead of spending tokens or freezing.

```python
class Theseus:
    """Nodo Ejecutor Determinista de Bajo Costo."""

    def __init__(self, sensor, motor, labyrinth, thread):
        self.sensor = sensor
        self.motor = motor
        self.labyrinth = labyrinth
        self.thread = thread

    async def __call__(self, state: dict) -> dict:
        print("--- ACTOR: Theseus (Fast Path) ---")

        if not await self.sensor.is_healthy():
            return {"errors": ["FatalError: El adaptador del navegador está caído o desconectado."]}

        try:
            snapshot = await self.sensor.perceive()
        except Exception as e:
            return {"errors": [f"SensorError: {e}"]}

        room_id = self.labyrinth.identify_room(snapshot)
        # ...
```

## Why this matters

1. `main.py` stays thin and orchestration-only.
2. Browser lifecycle ownership moves into the physical adapter where it belongs.
3. Health checks become just-in-time guards before action execution.
4. Mid-mission adapter crashes become explicit graph failures instead of undefined hangs.

## CLI consequence

Under this design, the CLI should only instantiate the adapter and run it with `async with adapter:`. Startup loops, polling, and process launch logic should be removed from `src/automation/main.py` and encapsulated in the adapter.
