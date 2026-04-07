"""Crawl4AI Apply Provider — High-Level Coordination.

This module orchestrates the application process for Crawl4AI. It handles 
map loading, semantic navigation, and delegates low-level execution 
to the C4AIReplayer.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from src.automation.ariadne.exceptions import (
    AriadneError,
    TerminalStateReached,
)
from src.automation.ariadne.models import (
    ApplyMeta,
    AriadnePortalMap,
)
from src.automation.ariadne.navigator import AriadneNavigator
from src.automation.motors.crawl4ai.replayer import C4AIReplayer
from src.automation.storage import AutomationStorage
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class Crawl4AIApplyProvider:
    """Standardized apply provider for Crawl4AI consuming Ariadne Maps."""

    def __init__(self, source_name: str, storage: Optional[AutomationStorage] = None) -> None:
        """Initializes the provider.
        
        Args:
            source_name: The portal identifier.
            storage: Optional AutomationStorage instance.
        """
        self.source_name = source_name
        self.storage = storage or AutomationStorage()
        self.replayer = C4AIReplayer()
        self._portal_map: Optional[AriadnePortalMap] = None
        self._navigator: Optional[AriadneNavigator] = None

    @property
    def portal_map(self) -> AriadnePortalMap:
        """Loads and returns the unified semantic map for this portal."""
        if not self._portal_map:
            map_path = Path(__file__).parent.parent.parent / "portals" / self.source_name / "maps" / "easy_apply.json"
            if not map_path.exists():
                raise FileNotFoundError(f"Ariadne Map not found for {self.source_name} at {map_path}")
            with open(map_path, "r") as f:
                self._portal_map = AriadnePortalMap.model_validate(json.load(f))
        return self._portal_map

    @property
    def navigator(self) -> AriadneNavigator:
        """Returns the semantic navigator."""
        if not self._navigator:
            self._navigator = AriadneNavigator(self.portal_map)
        return self._navigator

    def _browser_config(self, headless: bool = True) -> BrowserConfig:
        """Generates the injected BrowserOS configuration."""
        from src.automation.motors.browseros.injection import get_browseros_injected_config
        return get_browseros_injected_config(headless=headless)

    async def _get_live_state(self, session_id: str, crawler: AsyncWebCrawler) -> Optional[str]:
        """Identify current semantic state by checking the live DOM."""
        all_selectors = set()
        for state in self.portal_map.states.values():
            for target in state.presence_predicate.required_elements:
                if target.css: all_selectors.add(target.css)
        
        if not all_selectors:
            return None

        js_checks = ", ".join(f'"{sel}": !!document.querySelector({json.dumps(sel)})' for sel in all_selectors)
        js_code = f"return {{{js_checks}}};"
        results: dict[str, bool] = {}

        async def _check_hook(page: Any, **kwargs: Any) -> Any:
            nonlocal results
            results = await page.evaluate(js_code)
            return page

        await crawler.arun(
            url="about:blank",
            config=CrawlerRunConfig(js_only=True, session_id=session_id, hooks={"before_retrieve_html": _check_hook}),
        )
        return self.navigator.find_current_state(results)

    async def setup_session(self) -> None:
        """HITL session setup (e.g., login). Uses visible browser."""
        # This is a stub - in injection mode, BrowserOS handles visibility.
        logger.info("%s Setup session for %s requested. Perform manual login in BrowserOS.", LogTag.FAST, self.source_name)

    async def run(
        self,
        job_id: str,
        cv_path: Path,
        letter_path: Optional[Path] = None,
        dry_run: bool = False,
        path_id: str = "standard_easy_apply",
    ) -> ApplyMeta:
        """Executes the apply flow."""
        if self.storage.check_already_submitted(self.source_name, job_id):
            raise RuntimeError(f"Job {job_id} ({self.source_name}) was already submitted.")

        ingest_data = self.storage.get_job_state(self.source_name, job_id)
        application_url = ingest_data.get("application_url") or ingest_data.get("url")
        path = self.portal_map.paths.get(path_id)
        if not path:
            raise ValueError(f"Path '{path_id}' not found in map for {self.source_name}")

        # Build context
        context = {
            "profile": { "first_name": "Juan Pablo", "last_name": "Ruiz", "email": "jp@example.com", "phone": "+49123456789" },
            "job": { "job_title": ingest_data.get("job_title", ""), "company_name": ingest_data.get("company_name", ""), "application_url": application_url },
            "cv_path": str(cv_path),
            "letter_path": str(letter_path) if letter_path else None,
        }
        
        session_id = f"apply_c4a_{self.source_name}_{job_id}"
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            current_step_index = 1
            async with AsyncWebCrawler(config=self._browser_config()) as crawler:
                logger.info("%s Starting Crawl4AI Semantic Replay for %s", LogTag.FAST, self.source_name)
                
                while current_step_index <= len(path.steps):
                    step = path.steps[current_step_index - 1]
                    if dry_run and step.dry_run_stop:
                        logger.info("%s Dry-run stop at step '%s'", LogTag.OK, step.name)
                        break

                    # Observe and Check mission status
                    current_state = await self._get_live_state(session_id, crawler)
                    
                    # We might need page content for secondary mission verification
                    page_content = "" # In a real run, we'd extract text from the last result or DOM
                    
                    finished, mission_status = self.navigator.check_mission_status(
                        path.task_id, 
                        current_state or "",
                        page_content=page_content
                    )
                    if finished:
                        if mission_status == "terminal_failure":
                            raise TerminalStateReached(f"Reached failure state: {current_state}")
                        break

                    # Execute Step
                    result = await self.replayer.execute_step(
                        step=step,
                        crawler=crawler,
                        session_id=session_id,
                        context=context,
                        cv_path=cv_path,
                        letter_path=letter_path,
                        is_first_step=(current_step_index == 1),
                        application_url=application_url
                    )

                    if result.screenshot:
                        self.storage.write_artifact(
                            source=self.source_name, job_id=job_id,
                            filename=f"step_{current_step_index}_{step.name}.png", content=result.screenshot
                        )

                    # Advance
                    next_state = await self._get_live_state(session_id, crawler)
                    current_step_index = self.navigator.get_next_step_index(path, current_step_index, next_state)

                final_status = "submitted" if not dry_run else "dry_run"
                meta = ApplyMeta(status=final_status, timestamp=timestamp)
                self.storage.write_apply_meta(self.source_name, job_id, meta.model_dump())
                return meta

        except AriadneError as exc:
            logger.error("%s Ariadne Error: %s", LogTag.FAIL, exc)
            await self._capture_error_screenshot(session_id, job_id)
            meta = ApplyMeta(status="failed", timestamp=timestamp, error=str(exc))
            self.storage.write_apply_meta(self.source_name, job_id, meta.model_dump())
            raise
        except Exception as exc:
            logger.error("%s Unexpected Error: %s", LogTag.FAIL, exc)
            await self._capture_error_screenshot(session_id, job_id)
            raise

    async def _capture_error_screenshot(self, session_id: str, job_id: str) -> None:
        """Captures state on failure."""
        try:
            async with AsyncWebCrawler(config=self._browser_config()) as crawler:
                err_result = await crawler.arun(url="about:blank", config=CrawlerRunConfig(js_only=True, screenshot=True, session_id=session_id))
                if err_result.screenshot:
                    self.storage.write_artifact(source=self.source_name, job_id=job_id, filename="error_state.png", content=err_result.screenshot)
        except Exception: pass
