"""Crawl4AI Replayer — Low-Level Path Execution.

This module owns the motor-specific execution loop for Crawl4AI. 
It knows how to run a single AriadneStep or a sequence of steps 
using the C4AI compiler and the active browser session.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from src.automation.ariadne.exceptions import ObservationFailed
from src.automation.ariadne.models import (
    AriadneIntent,
    AriadnePath,
    AriadneStep,
)
from src.automation.motors.crawl4ai.compiler import AriadneC4AICompiler, C4AIScriptSerializer
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class C4AIReplayer:
    """Replays Ariadne Steps using the Crawl4AI motor."""

    def __init__(self):
        self.compiler = AriadneC4AICompiler()
        self.serializer = C4AIScriptSerializer()

    async def execute_step(
        self,
        step: AriadneStep,
        crawler: AsyncWebCrawler,
        session_id: str,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Optional[Path] = None,
        is_first_step: bool = False,
        application_url: Optional[str] = None,
    ) -> Any:
        """Executes a single Ariadne step."""
        
        # Identify if this step has an upload
        upload_selectors = [
            a.target.css for a in step.actions 
            if a.intent == AriadneIntent.UPLOAD and a.target and a.target.css
        ]
        
        # Compile step
        temp_path = AriadnePath(id="temp", task_id="temp", steps=[step])
        ir = self.compiler.compile(temp_path)
        raw_script = self.serializer.serialize(ir)
        
        # Render placeholders
        final_script = self._render_placeholders(raw_script, context)

        run_config = CrawlerRunConfig(
            c4a_script=final_script,
            session_id=session_id,
            screenshot=True,
        )

        if upload_selectors:
            run_config.hooks = {
                "before_retrieve_html": self._build_file_upload_hook(cv_path, letter_path, upload_selectors)
            }

        url = application_url if is_first_step and application_url else "about:blank"
        
        result = await crawler.arun(url=url, config=run_config)

        if not result.success:
            raise ObservationFailed(
                f"Step {step.name} execution failed: {result.error_message}", 
                step_index=step.step_index
            )
            
        return result

    def _render_placeholders(self, text: str, context: dict) -> str:
        """Inject context values into {{placeholder}} strings."""
        result = text
        for key, value in context.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    placeholder = f"{{{{{key}.{k}}}}}"
                    if placeholder in result:
                        result = result.replace(placeholder, str(v) if v is not None else "")
            else:
                placeholder = "{{" + key + "}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value) if value is not None else "")
        return result

    def _build_file_upload_hook(self, cv_path: Path, letter_path: Path | None, upload_selectors: list[str]):
        """Return a hook that performs file uploads via raw Playwright."""
        async def _hook(page: Any, **kwargs: Any) -> Any:
            for selector in upload_selectors:
                await page.set_input_files(selector, str(cv_path))
            return page
        return _hook
