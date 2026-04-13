"""Crawl4AI Adapter Implementation — Crawl4AI-based Periphery."""

from typing import Optional, Dict, Any, List
import base64

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

from src.automation.ariadne.core.periphery import BrowserAdapter
from src.automation.ariadne.contracts.base import (
    CrawlCommand,
    ExecutionResult,
    MotorCommand,
    SnapshotResult,
    ScriptCommand
)


class Crawl4AIAdapter(BrowserAdapter):
    """
    Implements Sensor, Motor and PeripheralAdapter for Crawl4AI.
    Manages the lifecycle of a single AsyncWebCrawler session.
    """

    def __init__(self, session_id: str = "ariadne-session"):
        """
        Initialize the adapter.
        
        Args:
            session_id: The session ID for the underlying crawler.
        """
        self._session_id = session_id
        self._crawler: Optional[AsyncWebCrawler] = None
        self._current_url: str = "about:blank"

    async def is_healthy(self) -> bool:
        """Checks if the crawler is open and ready."""
        return self._crawler is not None

    async def __aenter__(self) -> "Crawl4AIAdapter":
        """
        Creates the persistent browser session on context entry.
        Ensures a single browser context per mission.
        """
        if self._crawler is None:
            self._crawler = AsyncWebCrawler()
            await self._crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Closes the browser session on context exit."""
        if self._crawler is not None:
            await self._crawler.__aexit__(exc_type, exc_val, exc_tb)
            self._crawler = None

    async def perceive(self) -> SnapshotResult:
        """Captures the current browser state via Crawl4AI."""
        if not self._crawler:
            raise RuntimeError("Crawl4AIAdapter must be used within an 'async with' block.")

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            screenshot=True,
            process_iframes=True,
            session_id=self._session_id,
        )
        
        # Use the last known URL to avoid redundant navigation if possible
        result = await self._crawler.arun(url=self._current_url, config=config)

        screenshot_b64 = None
        if result.success and hasattr(result, "screenshot") and result.screenshot:
            screenshot_b64 = result.screenshot

        return SnapshotResult(
            url=result.url or self._current_url,
            dom_elements=[],  # DOM elements mapping would go here
            screenshot_b64=screenshot_b64,
        )

    async def act(self, command: MotorCommand) -> ExecutionResult:
        """Executes a motor command via Crawl4AI scripts."""
        if not self._crawler:
            raise RuntimeError("Crawl4AIAdapter must be used within an 'async with' block.")
            
        if isinstance(command, ScriptCommand):
            return await self._execute_js(command.script)
            
        if not isinstance(command, CrawlCommand):
            return ExecutionResult(status="failed", error=f"Unsupported command: {type(command)}")

        try:
            config = CrawlerRunConfig(
                c4a_script=command.c4a_script,
                cache_mode=CacheMode.BYPASS,
                screenshot=True,
                return_js_script_result=True,
                session_id=self._session_id,
            )

            result = await self._crawler.arun(url=self._current_url, config=config)

            if result.success:
                self._current_url = result.url or self._current_url
                script_result = result.js_script_result

                # Handle failure indices in batch scripts
                if isinstance(script_result, dict) and "failed_at" in script_result:
                    return ExecutionResult(
                        status="failed",
                        failed_at_index=script_result.get("failed_at"),
                        completed_count=script_result.get("completed_count"),
                        error=script_result.get("error")
                    )

                return ExecutionResult(
                    status="success",
                    extracted_data=script_result if isinstance(script_result, dict) else {"result": script_result}
                )
            else:
                return ExecutionResult(status="failed", error=result.error_message)
        except Exception as e:
            return ExecutionResult(status="failed", error=str(e))

    async def _execute_js(self, script: str) -> ExecutionResult:
        """Helper to run arbitrary JS via the crawler."""
        try:
            config = CrawlerRunConfig(
                js_code=script,
                cache_mode=CacheMode.BYPASS,
                session_id=self._session_id,
            )
            result = await self._crawler.arun(url=self._current_url, config=config)
            
            if result.success:
                return ExecutionResult(
                    status="success",
                    extracted_data={"result": result.js_result}
                )
            return ExecutionResult(status="failed", error=result.error_message)
        except Exception as e:
            return ExecutionResult(status="failed", error=str(e))
