"""Shared base class for auto-application adapters.

Adapters provide portal-specific knowledge only (selectors, C4A-Scripts, profile dir).
All flow control lives here: navigate → validate → fill → upload → submit → persist.

Design reference: `src/automation/motors/crawl4ai/`

Crawl4AI docs:
  C4A-Script DSL:    https://docs.crawl4ai.com/core/c4a-script/
  CrawlerRunConfig:  https://docs.crawl4ai.com/api/parameters/
  Hooks:             https://docs.crawl4ai.com/advanced/hooks-auth/
  Session mgmt:      https://docs.crawl4ai.com/advanced/session-management/
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from src.automation.ariadne.models import AriadnePortalMap, AriadnePath, AriadneTask, AriadneStep, AriadneIntent
from src.automation.ariadne.compiler.c4ai.compiler import AriadneC4AICompiler
from src.automation.ariadne.compiler.c4ai.serializer import C4AIScriptSerializer
from src.automation.ariadne.exceptions import (
    AriadneError,
    ObservationFailed,
    TargetNotFound,
    TaskAborted,
    TerminalStateReached,
)
from src.automation.ariadne.navigator import AriadneNavigator
from src.automation.motors.crawl4ai.models import ApplicationRecord, ApplyMeta
from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class ApplyAdapter(ABC):
    """Abstract base class for deterministic portal-specific apply adapters.

    Now uses AriadnePortalMap as the source of truth for states, tasks, and paths.
    """

    def __init__(self, data_manager: DataManager | None = None) -> None:
        self.data_manager = data_manager or DataManager()
        self.compiler = AriadneC4AICompiler()
        self.serializer = C4AIScriptSerializer()
        self._navigator: Optional[AriadneNavigator] = None

    @property
    @abstractmethod
    def portal_map(self) -> AriadnePortalMap:
        """The unified semantic map for this portal."""

    @property
    def navigator(self) -> AriadneNavigator:
        if not self._navigator:
            self._navigator = AriadneNavigator(self.portal_map)
        return self._navigator

    @property
    def source_name(self) -> str:
        return self.portal_map.portal_name

    def _get_portal_base_url(self) -> str:
        return self.portal_map.base_url

    @abstractmethod
    def get_session_profile_dir(self) -> Path:
        """Path to the persistent browser profile directory for this portal."""

    @abstractmethod
    def get_success_text(self) -> str:
        """Text fragment expected in the confirmation page content."""

    # ── Pure helpers ────────────────────────────────────────────────────────

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

    def _check_idempotency(self, job_id: str) -> None:
        try:
            meta = self.data_manager.read_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name="apply",
                stage="meta",
                filename="apply_meta.json",
            )
        except (FileNotFoundError, KeyError):
            return
        if meta.get("status") == "submitted":
            raise RuntimeError(f"Job {job_id} ({self.source_name}) was already submitted.")

    # ── crawl4ai helpers ─────────────────────────────────────────────────────

    def _browser_config(self, headless: bool = True) -> BrowserConfig:
        return BrowserConfig(
            user_data_dir=str(self.get_session_profile_dir()),
            use_persistent_context=True,
            headless=headless,
        )

    async def _get_live_state(self, session_id: str) -> Optional[str]:
        """Identify current semantic state by checking the live DOM."""
        # Get all relevant selectors from the map
        all_selectors = set()
        for state in self.portal_map.states.values():
            for target in state.presence_predicate.required_elements:
                if target.css: all_selectors.add(target.css)
        
        if not all_selectors:
            return None

        js_checks = ", ".join(
            f'"{sel}": !!document.querySelector({json.dumps(sel)})'
            for sel in all_selectors
        )
        js_code = f"return {{{js_checks}}};"

        results: dict[str, bool] = {}

        async def _check_hook(page: Any, **kwargs: Any) -> Any:
            nonlocal results
            results = await page.evaluate(js_code)
            return page

        async with AsyncWebCrawler(config=self._browser_config()) as crawler:
            await crawler.arun(
                url="about:blank",
                config=CrawlerRunConfig(
                    js_only=True,
                    session_id=session_id,
                    hooks={"before_retrieve_html": _check_hook},
                ),
            )
        
        return self.navigator.find_current_state(results)

    def _build_file_upload_hook(self, cv_path: Path, letter_path: Path | None, upload_selectors: list[str]):
        """Return a hook that performs file uploads via raw Playwright."""
        async def _hook(page: Any, **kwargs: Any) -> Any:
            for selector in upload_selectors:
                await page.set_input_files(selector, str(cv_path))
            return page
        return _hook

    async def _capture_error_screenshot(self, session_id: str, job_id: str) -> None:
        """Best-effort capture of the page state on failure."""
        try:
            async with AsyncWebCrawler(config=self._browser_config()) as crawler:
                err_result = await crawler.arun(
                    url="about:blank",
                    config=CrawlerRunConfig(
                        js_only=True,
                        screenshot=True,
                        session_id=session_id,
                    ),
                )
                if err_result.screenshot:
                    self.data_manager.write_bytes_artifact(
                        source=self.source_name, job_id=job_id, node_name="apply", stage="proposed",
                        filename="error_state.png", content=err_result.screenshot
                    )
        except Exception as e:
            logger.warning("%s Failed to capture error screenshot: %s", LogTag.WARN, e)

    # ── Execution ──────────────────────────────────────────────────────────

    def _build_context(self, ingest_data: dict, cv_path: Path, letter_path: Path | None) -> dict:
        return {
            "profile": {
                "first_name": "Juan Pablo",
                "last_name": "Ruiz",
                "email": "jp@example.com",
                "phone": "+49123456789",
            },
            "job": {
                "job_title": ingest_data.get("job_title", ""),
                "company_name": ingest_data.get("company_name", ""),
                "application_url": ingest_data.get("application_url", ""),
            },
            "cv_path": str(cv_path),
            "letter_path": str(letter_path) if letter_path else None,
        }

    async def run(
        self,
        job_id: str,
        cv_path: Path,
        letter_path: Path | None,
        dry_run: bool,
        path_id: str = "standard_easy_apply",
    ) -> ApplyMeta:
        """Execute the full apply flow using the Ariadne Map."""
        self._check_idempotency(job_id)

        ingest_data = self.data_manager.read_json_artifact(
            source=self.source_name, job_id=job_id, node_name="ingest", stage="proposed", filename="state.json"
        )
        application_url = ingest_data.get("application_url") or ingest_data.get("url")
        
        path = self.portal_map.paths.get(path_id)
        if not path:
            raise ValueError(f"Path '{path_id}' not found in map for {self.source_name}")

        context = self._build_context(ingest_data, cv_path, letter_path)
        session_id = f"apply_{self.source_name}_{job_id}"
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            current_step_index = 1
            async with AsyncWebCrawler(config=self._browser_config()) as crawler:
                logger.info("%s Starting Semantic Replay for %s/%s", LogTag.FAST, self.source_name, job_id)
                
                while current_step_index <= len(path.steps):
                    step = path.steps[current_step_index - 1]
                    
                    if dry_run and step.dry_run_stop:
                        logger.info("%s Dry-run stop reached at step '%s'", LogTag.OK, step.name)
                        break

                    # 1. State Identification (Optional check before step)
                    current_state = await self._get_live_state(session_id)
                    
                    # 2. Check Mission Status
                    finished, status = self.navigator.check_mission_status(path.task_id, current_state or "")
                    if finished:
                        logger.info("%s Mission Finished with status: %s", LogTag.OK, status)
                        if status == "terminal_failure":
                            raise TerminalStateReached(f"Reached failure state: {current_state}")
                        break

                    # 3. Execution
                    upload_selectors = [a.target.css for a in step.actions if a.intent == AriadneIntent.UPLOAD and a.target and a.target.css]
                    temp_path = AriadnePath(id="temp", task_id=path.task_id, steps=[step])
                    ir = self.compiler.compile(temp_path)
                    raw_script = self.serializer.serialize(ir)
                    final_script = self._render_placeholders(raw_script, context)

                    run_config = CrawlerRunConfig(
                        c4a_script=final_script,
                        session_id=session_id,
                        screenshot=True,
                    )
                    if upload_selectors:
                        run_config.hooks = {"before_retrieve_html": self._build_file_upload_hook(cv_path, letter_path, upload_selectors)}

                    result = await crawler.arun(
                        url=application_url if current_step_index == 1 else "about:blank",
                        config=run_config
                    )

                    if not result.success:
                        raise ObservationFailed(f"Step {step.name} execution failed: {result.error_message}", step_index=current_step_index)

                    if result.screenshot:
                        self.data_manager.write_bytes_artifact(
                            source=self.source_name, job_id=job_id, node_name="apply", stage="proposed",
                            filename=f"step_{current_step_index}_{step.name}.png", content=result.screenshot
                        )

                    # 4. Determine next step via Navigator
                    next_state = await self._get_live_state(session_id)
                    current_step_index = self.navigator.get_next_step_index(path, current_step_index, next_state)

                status = "submitted" if not dry_run else "dry_run"
                meta = ApplyMeta(status=status, timestamp=timestamp)
                self.data_manager.write_json_artifact(
                    source=self.source_name, job_id=job_id, node_name="apply", stage="meta",
                    filename="apply_meta.json", data=meta.model_dump()
                )
                return meta

        except AriadneError as exc:
            logger.error("%s Ariadne Error: %s", LogTag.FAIL, exc)
            await self._capture_error_screenshot(session_id, job_id)
            meta = ApplyMeta(status="failed", timestamp=timestamp, error=str(exc))
            self.data_manager.write_json_artifact(
                source=self.source_name, job_id=job_id, node_name="apply", stage="meta",
                filename="apply_meta.json", data=meta.model_dump()
            )
            raise
        except Exception as exc:
            logger.error("%s Unexpected Error: %s", LogTag.FAIL, exc)
            await self._capture_error_screenshot(session_id, job_id)
            raise

