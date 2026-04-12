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
    """

    def __init__(self):
        self.current_url = "about:blank"

    async def take_snapshot(self) -> SnapshotResult:
        """Captures the current browser state via Crawl4AI."""
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                screenshot=True,
                process_iframes=True
            )
            result = await crawler.arun(url=self.current_url, config=config)
            
            screenshot_b64 = None
            if result.success and hasattr(result, 'screenshot') and result.screenshot:
                screenshot_b64 = result.screenshot

            return SnapshotResult(
                url=result.url or self.current_url,
                dom_elements=[], # DOM elements mapping would go here
                screenshot_b64=screenshot_b64
            )

    async def execute(self, command: MotorCommand) -> ExecutionResult:
        """Runs a JIT command or batch via Crawl4AI."""
        if not isinstance(command, CrawlCommand):
            return ExecutionResult(
                status="failed",
                error=f"Invalid command type: {type(command)}"
            )

        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(
                    c4a_script=command.c4a_script,
                    cache_mode=CacheMode.BYPASS,
                    screenshot=True,
                    return_js_script_result=True, # Important to get script return value
                )

                result = await crawler.arun(url=self.current_url, config=config)

                if result.success:
                    self.current_url = result.url or self.current_url
                    script_result = result.js_script_result
                    
                    # If the script returns a dict, it's a failure index
                    if isinstance(script_result, dict) and 'failed_at' in script_result:
                        return ExecutionResult(
                            status="failed",
                            failed_at_index=script_result.get('failed_at'),
                            error=script_result.get('error', 'Action failed in batch')
                        )

                    # If script result is None or not a dict, it's full success
                    return ExecutionResult(status="success")
                else:
                    # This means the entire batch failed to even start or run
                    return ExecutionResult(
                        status="failed",
                        error=getattr(result, 'error_message', 'Unknown Crawl4AI error')
                    )
        except Exception as e:
            return ExecutionResult(status="failed", error=str(e))
