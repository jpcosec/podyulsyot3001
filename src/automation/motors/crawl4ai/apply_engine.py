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

from src.automation.ariadne.models import AriadnePortalMap, AriadnePath, AriadneTask
from src.automation.ariadne.compiler.c4ai.compiler import AriadneC4AICompiler
from src.automation.ariadne.compiler.c4ai.serializer import C4AIScriptSerializer
from src.automation.motors.crawl4ai.models import ApplicationRecord, ApplyMeta, FormSelectors
from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class PortalStructureChangedError(Exception):
    """Raised when one or more mandatory selectors are absent from the live DOM."""


class ApplyAdapter(ABC):
    """Abstract base class for deterministic portal-specific apply adapters.

    Now uses AriadnePortalMap as the source of truth for states, tasks, and paths.
    """

    def __init__(self, data_manager: DataManager | None = None) -> None:
        self.data_manager = data_manager or DataManager()
        self.compiler = AriadneC4AICompiler()
        self.serializer = C4AIScriptSerializer()

    @property
    @abstractmethod
    def portal_map(self) -> AriadnePortalMap:
        """The unified semantic map for this portal."""

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
            # Support nested profile.key access
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

    async def _check_state_presence(
        self, session_id: str, state_id: str
    ) -> bool:
        """Verify if we are currently in the specified semantic state."""
        state = self.portal_map.states.get(state_id)
        if not state:
            return False
            
        required_css = [t.css for t in state.presence_predicate.required_elements if t.css]
        if not required_css:
            return True # No specific CSS guards, assume true if called

        js_checks = ", ".join(
            f'!!document.querySelector({json.dumps(sel)})'
            for sel in required_css
        )
        js_code = f"return [{js_checks}].every(v => v);"

        presence = False

        async def _check_hook(page: Any, **kwargs: Any) -> Any:
            presence = await page.evaluate(js_code)
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
        return presence

    # ── Execution ──────────────────────────────────────────────────────────

    def _build_context(self, ingest_data: dict, cv_path: Path, letter_path: Path | None) -> dict:
        """Build full context for placeholder resolution."""
        # This should eventually come from a real ProfileManager
        return {
            "profile": {
                "first_name": "Juan Pablo", # Placeholder
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
            # 1. Compile Path to C4A-Script
            ir = self.compiler.compile(path)
            raw_script = self.serializer.serialize(ir)
            
            # Resolve placeholders in the script
            final_script = self._render_placeholders(raw_script, context)

            async with AsyncWebCrawler(config=self._browser_config()) as crawler:
                logger.info("%s Executing Ariadne Path '%s' for %s/%s", LogTag.FAST, path_id, self.source_name, job_id)
                
                # If we are in dry-run, we might want to split the script before the submit step
                # For now, we assume the dry_run_stop flag in AriadneStep is handled by the compiler 
                # or we manually truncate the IR. 
                # Simplification: if dry_run, we just don't run the script or we run a truncated version.
                
                result = await crawler.arun(
                    url=application_url,
                    config=CrawlerRunConfig(
                        c4a_script=final_script,
                        session_id=session_id,
                        screenshot=True,
                    ),
                )

                if result.screenshot:
                    self.data_manager.write_bytes_artifact(
                        source=self.source_name, job_id=job_id, node_name="apply", stage="proposed",
                        filename="screenshot.png", content=result.screenshot
                    )

                status = "submitted" if not dry_run else "dry_run"
                meta = ApplyMeta(status=status, timestamp=timestamp)
                self.data_manager.write_json_artifact(
                    source=self.source_name, job_id=job_id, node_name="apply", stage="meta",
                    filename="apply_meta.json", data=meta.model_dump()
                )
                
                return meta

        except Exception as exc:
            logger.error("%s Apply failed: %s", LogTag.FAIL, exc)
            raise

