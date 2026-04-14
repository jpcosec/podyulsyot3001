"""BrowserOSAdapter — Sensor + Motor backed by Crawl4AI connected to BrowserOS.

BrowserOS ports (from config.sample.json):
  9000  CDP WebSocket  →  Crawl4AI connects here (this file)
  9100  HTTP MCP       →  health check + Delphi cold path
  9200  Agent API      →  BrowserOS native agent / passive recording
  9300  Extension      →  internal Chromium extension
"""

from __future__ import annotations

import asyncio
import subprocess
from typing import Optional

import httpx
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from src.automation.contracts.sensor import Sensor, SnapshotResult
from src.automation.contracts.motor import Motor, MotorCommand, ExecutionResult, TraceEvent

CDP_URL = "ws://localhost:9000"
MCP_URL = "http://localhost:9100"
STARTUP_TIMEOUT_S = 30


class BrowserOSAdapter:
    """Implements Sensor and Motor by connecting Crawl4AI to BrowserOS's Chromium."""

    def __init__(self, session_id: str, appimage_path: Optional[str] = None):
        self._session_id = session_id
        self._appimage_path = appimage_path
        self._process: Optional[subprocess.Popen] = None
        self._crawler: Optional[AsyncWebCrawler] = None
        self._current_url: str = "about:blank"

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                resp = await client.get(f"{MCP_URL}/health")
                return resp.status_code == 200
        except Exception:
            return False

    async def __aenter__(self) -> "BrowserOSAdapter":
        await self._ensure_browseros_running()
        browser_config = BrowserConfig(cdp_url=CDP_URL)
        self._crawler = AsyncWebCrawler(config=browser_config)
        await self._crawler.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        if self._crawler:
            await self._crawler.__aexit__(*args)
        if self._process:
            self._process.kill()

    async def _ensure_browseros_running(self) -> None:
        if await self.is_healthy():
            return
        if not self._appimage_path:
            raise RuntimeError(f"BrowserOS not responding at {MCP_URL} and no appimage_path provided.")
        self._process = subprocess.Popen(
            [self._appimage_path, "--no-sandbox"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(STARTUP_TIMEOUT_S):
            await asyncio.sleep(1)
            if await self.is_healthy():
                return
        self._process.kill()
        raise TimeoutError(f"BrowserOS failed to start after {STARTUP_TIMEOUT_S}s.")

    # ── Sensor ───────────────────────────────────────────────────────────────

    async def perceive(self, *, with_screenshot: bool = False) -> SnapshotResult:
        config = CrawlerRunConfig(
            session_id=self._session_id,
            js_only=True,
            screenshot=with_screenshot,
            cache_mode=CacheMode.BYPASS,
        )
        result = await self._crawler.arun(self._current_url, config=config)
        return SnapshotResult(
            url=result.url or self._current_url,
            html=result.cleaned_html or result.html or "",
            screenshot_b64=result.screenshot if with_screenshot else None,
            links=[lnk["href"] for lnk in result.links.get("internal", []) if lnk.get("href")],
            status_code=result.status_code or 200,
        )

    # ── Motor ────────────────────────────────────────────────────────────────

    async def act(self, command: MotorCommand) -> ExecutionResult:
        if command.operation == "navigate":
            return await self._navigate(command)
        if command.operation == "extract":
            return await self._extract(command)
        return await self._execute_js(command)

    async def _navigate(self, command: MotorCommand) -> ExecutionResult:
        config = CrawlerRunConfig(
            session_id=self._session_id,
            wait_for=command.wait_for,
            cache_mode=CacheMode.BYPASS,
        )
        result = await self._crawler.arun(command.value, config=config)
        if result.success:
            self._current_url = result.url
        return self._build_result(command, result.success, result.error_message)

    async def _execute_js(self, command: MotorCommand) -> ExecutionResult:
        config = CrawlerRunConfig(
            session_id=self._session_id,
            js_only=True,
            js_code=_js_for(command),
            wait_for=command.wait_for,
            cache_mode=CacheMode.BYPASS,
        )
        result = await self._crawler.arun(self._current_url, config=config)
        return self._build_result(command, result.success, result.error_message)

    async def _extract(self, command: MotorCommand) -> ExecutionResult:
        # command.value carries the JSON schema id — caller must resolve it to a
        # JsonCssExtractionStrategy before calling act(). Placeholder for now.
        raise NotImplementedError("ExtractionAction must provide a pre-built strategy — see PortalDictionary.")

    @staticmethod
    def _build_result(command: MotorCommand, success: bool, error: Optional[str]) -> ExecutionResult:
        trace = TraceEvent(command=command, success=success, error=error)
        return ExecutionResult(success=success, trace_event=trace, error=error)


# ── JS builder (pure function, no state) ─────────────────────────────────────

def _js_for(command: MotorCommand) -> str:
    sel = command.selector.replace("'", "\\'")
    match command.operation:
        case "click":
            return f"document.querySelector('{sel}').click();"
        case "fill":
            val = (command.value or "").replace("'", "\\'")
            return f"document.querySelector('{sel}').value = '{val}';"
        case "submit":
            return f"document.querySelector('{sel}').submit();"
        case "scroll":
            return "window.scrollTo(0, document.body.scrollHeight);"
        case "wait":
            return ""
        case _:
            raise ValueError(f"No JS mapping for operation '{command.operation}'")
