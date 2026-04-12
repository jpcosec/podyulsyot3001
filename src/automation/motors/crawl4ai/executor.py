"""Crawl4AI JIT Executor Implementation."""

from typing import Any, Dict, Optional, List
import base64

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

from src.automation.ariadne.contracts.base import (
    CrawlCommand,
    ExecutionResult,
    Executor,
    MotorCommand,
    SnapshotResult,
)


class Crawl4AIExecutor(Executor):
    """
    JIT Executor for Crawl4AI.
    Executes atomic or batched C4A-Scripts.
    Maintains a persistent browser session across LangGraph runs.
    """

    def __init__(self):
        self.current_url = "about:blank"
        self._crawler: Optional[AsyncWebCrawler] = None
        self._session_id = "ariadne-session"

    async def __aenter__(self) -> "Crawl4AIExecutor":
        """Create persistent crawler session on entry."""
        self._crawler = AsyncWebCrawler()
        await self._crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Destroy crawler session on exit."""
        if self._crawler is not None:
            await self._crawler.__aexit__(exc_type, exc_val, exc_tb)
            self._crawler = None

    async def take_snapshot(self) -> SnapshotResult:
        """Captures the current browser state via Crawl4AI."""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            screenshot=True,
            process_iframes=True,
            session_id=self._session_id,
        )
        result = await self._crawler.arun(url=self.current_url, config=config)

        screenshot_b64 = None
        if result.success and hasattr(result, "screenshot") and result.screenshot:
            screenshot_b64 = result.screenshot

        return SnapshotResult(
            url=result.url or self.current_url,
            dom_elements=[],  # DOM elements mapping would go here
            screenshot_b64=screenshot_b64,
        )

    async def execute(self, command: MotorCommand) -> ExecutionResult:
        """Runs a JIT command or batch via Crawl4AI."""
        if not isinstance(command, CrawlCommand):
            return ExecutionResult(
                status="failed", error=f"Invalid command type: {type(command)}"
            )

        try:
            config = CrawlerRunConfig(
                c4a_script=command.c4a_script,
                cache_mode=CacheMode.BYPASS,
                screenshot=True,
                return_js_script_result=True,  # Important to get script return value
                session_id=self._session_id,
            )

            result = await self._crawler.arun(url=self.current_url, config=config)

            if result.success:
                self.current_url = result.url or self.current_url
                script_result = result.js_script_result

                # If the script returns a dict, it's a failure index
                if isinstance(script_result, dict) and "failed_at" in script_result:
                    return ExecutionResult(
                        status="failed",
                        failed_at_index=script_result.get("failed_at"),
                        completed_count=script_result.get("completed_count"),
                        error=script_result.get("error", "Action failed in batch"),
                    )

                if (
                    isinstance(script_result, dict)
                    and "completed_count" in script_result
                ):
                    return ExecutionResult(
                        status="success",
                        completed_count=script_result.get("completed_count"),
                    )

                # If script result is None or not a dict, it's full success
                return ExecutionResult(status="success")
            else:
                # This means the entire batch failed to even start or run
                return ExecutionResult(
                    status="failed",
                    error=getattr(result, "error_message", "Unknown Crawl4AI error"),
                )
        except Exception as e:
            return ExecutionResult(status="failed", error=str(e))
