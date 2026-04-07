"""Crawl4AI Motor Provider — Browser adapter for Ariadne.

Implements MotorProvider / MotorSession for the Crawl4AI backend.
Orchestration (map loading, navigation, run loop) is owned by AriadneSession.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from src.automation.ariadne.exceptions import ObservationFailed
from src.automation.ariadne.models import AriadneStep
from src.automation.motors.crawl4ai.replayer import C4AIReplayer


class C4AIMotorSession:
    """Single-session adapter: observe DOM and execute steps via Crawl4AI."""

    def __init__(
        self,
        crawler: AsyncWebCrawler,
        session_id: str,
        replayer: C4AIReplayer,
    ) -> None:
        self._crawler = crawler
        self._session_id = session_id
        self._replayer = replayer

    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        """Check which CSS selectors are present in the live page.

        Args:
            selectors: CSS selectors to probe in the active browser session.

        Returns:
            Mapping of selector to a boolean indicating whether it is present.

        Raises:
            ObservationFailed: If the observation hook does not produce any result.
        """
        if not selectors:
            return {}

        js_checks = ", ".join(
            f"{json.dumps(sel)}: !!document.querySelector({json.dumps(sel)})"
            for sel in selectors
        )
        js_code = f"return {{{js_checks}}};"
        results: dict[str, bool] = {}

        async def _check_hook(page: Any, **kwargs: Any) -> Any:
            nonlocal results
            results = await page.evaluate(js_code)
            return page

        await self._crawler.arun(
            url="about:blank",
            config=CrawlerRunConfig(
                js_only=True,
                session_id=self._session_id,
                hooks={"before_retrieve_html": _check_hook},
            ),
        )
        if not results:
            raise ObservationFailed(
                "observe() returned empty results — hook may not have fired"
            )
        return results

    async def execute_step(
        self,
        step: AriadneStep,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        is_first: bool,
        url: str | None,
    ) -> None:
        """Execute a single AriadneStep via C4AIReplayer.

        Args:
            step: The semantic step to replay.
            context: Template context used to render action values.
            cv_path: Local CV path for upload actions.
            letter_path: Optional local cover letter path.
            is_first: Whether this is the first step in the replay loop.
            url: Application URL used for first-step navigation when needed.
        """
        await self._replayer.execute_step(
            step=step,
            crawler=self._crawler,
            session_id=self._session_id,
            context=context,
            cv_path=cv_path,
            letter_path=letter_path,
            is_first_step=is_first,
            application_url=url,
        )

    async def begin_human_intervention(
        self,
        artifact_dir: Path,
        step: AriadneStep,
        reason: str,
    ) -> dict[str, Any]:
        """Return minimal HITL context for Crawl4AI-backed sessions."""
        return {
            "artifact_dir": str(artifact_dir),
            "session_id": self._session_id,
            "reason": reason,
            "step_name": step.name,
        }


class C4AIMotorProvider:
    """Opens Crawl4AI browser sessions for AriadneSession.

    Usage::

        motor = C4AIMotorProvider()
        session = AriadneSession("linkedin")
        meta = await session.run(motor, job_id="123", cv_path=Path("cv.pdf"))
    """

    @asynccontextmanager
    async def open_session(self, session_id: str) -> AsyncIterator[C4AIMotorSession]:
        """Open a Crawl4AI browser session.

        Args:
            session_id: Unique session name (used for tab/CDP reuse).

        Yields:
            C4AIMotorSession ready to observe and execute steps.
        """
        async with AsyncWebCrawler(config=self._browser_config()) as crawler:
            yield C4AIMotorSession(crawler, session_id, C4AIReplayer())

    def _browser_config(self, headless: bool = True) -> BrowserConfig:
        from src.automation.motors.crawl4ai.browser_config import (
            get_browseros_injected_config,
        )

        return get_browseros_injected_config(headless=headless)
