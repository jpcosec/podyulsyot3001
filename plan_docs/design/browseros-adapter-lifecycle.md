# BrowserOS Adapter Lifecycle Draft

This design note captures the lifecycle responsibilities of a BrowserOS adapter and the expectation that runtime health checks belong to the physical adapter layer, not the CLI.

## Core idea

The logic for launching BrowserOS, polling `http://127.0.0.1:9000/mcp`, and validating runtime health should live inside the BrowserOS adapter itself. Keeping that logic in `main.py` is a lifecycle anti-pattern because it mixes CLI orchestration with physical adapter concerns.

## Proposed `BrowserOSAdapter`

```python
import asyncio
import subprocess
import requests
from typing import Optional
from src.automation.ariadne.contracts.base import SnapshotResult, ExecutionResult, MotorCommand

class BrowserOSAdapter:
    """Implementa Sensor, Motor y PeripheralAdapter para BrowserOS."""

    def __init__(self, base_url: str = "http://127.0.0.1:9000", appimage_path: Optional[str] = None):
        self.base_url = base_url
        self.appimage_path = appimage_path
        self._process: Optional[subprocess.Popen] = None
        self._tools_cache = None

    async def is_healthy(self) -> bool:
        """Comprueba si el servidor MCP de BrowserOS responde."""
        try:
            resp = await asyncio.to_thread(requests.get, f"{self.base_url}/mcp", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    async def __aenter__(self) -> "BrowserOSAdapter":
        """Asegura que BrowserOS esté arriba antes de inyectarlo en LangGraph."""
        if await self.is_healthy():
            return self

        if not self.appimage_path:
            raise RuntimeError(f"BrowserOS no responde en {self.base_url} y no hay AppImage para levantarlo.")

        print(f"[⚙️] Levantando BrowserOS desde {self.appimage_path}...")
        self._process = subprocess.Popen(
            [self.appimage_path, "--no-sandbox"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(30):
            await asyncio.sleep(1)
            if await self.is_healthy():
                print("[✅] BrowserOS listo y conectado.")
                return self

        self._kill_process()
        raise TimeoutError("BrowserOS falló al iniciar después de 30 segundos.")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Limpieza opcional."""
        pass

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
