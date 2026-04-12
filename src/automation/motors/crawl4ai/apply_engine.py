"""Crawl4AI Motor Provider — Browser adapter for Ariadne.

Implements MotorProvider / MotorSession for the Crawl4AI backend.
Orchestration (map loading, navigation, run loop) is owned by AriadneSession.
"""

from __future__ import annotations

import json
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from src.automation.ariadne.danger_contracts import (
    ApplyDangerReport,
    ApplyDangerSignals,
)
from src.automation.ariadne.danger_detection import ApplyDangerDetector
from src.automation.ariadne.exceptions import ObservationFailed
from src.automation.ariadne.models import AriadneStep
from src.automation.credentials import ResolvedPortalCredentials
from src.automation.motors.crawl4ai.replayer import C4AIReplayer
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class C4AIMotorSession:
    """Single-session adapter: observe DOM and execute steps via Crawl4AI."""

    def __init__(
        self,
        crawler: AsyncWebCrawler,
        session_id: str,
        replayer: C4AIReplayer,
        credentials: ResolvedPortalCredentials | None = None,
    ) -> None:
        self._crawler = crawler
        self._session_id = session_id
        self._replayer = replayer
        self._credentials = credentials
        self._danger_detector = ApplyDangerDetector()

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

        self._crawler.crawler_strategy.set_hook("before_retrieve_html", _check_hook)
        try:
            await self._crawler.arun(
                url="raw:",
                config=CrawlerRunConfig(
                    js_only=True,
                    session_id=self._session_id,
                ),
            )
        finally:
            self._crawler.crawler_strategy.set_hook("before_retrieve_html", None)
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

    async def inspect_danger(self, application_url: str | None) -> ApplyDangerReport:
        """Inspect the current Crawl4AI page for risky apply-flow states."""
        signals = ApplyDangerSignals(application_url=application_url)

        async def _inspect_hook(page: Any, **kwargs: Any) -> Any:
            signals.current_url = await page.evaluate("window.location.href")
            signals.dom_text = await page.evaluate(
                "document.body ? document.body.innerText : ''"
            )
            return page

        self._crawler.crawler_strategy.set_hook("before_retrieve_html", _inspect_hook)
        try:
            await self._crawler.arun(
                url="raw:",
                config=CrawlerRunConfig(
                    js_only=True,
                    session_id=self._session_id,
                ),
            )
        finally:
            self._crawler.crawler_strategy.set_hook("before_retrieve_html", None)
        return self._danger_detector.detect(signals)

    async def highlight_element(self, selector: str, color: str = "red") -> None:
        """Draw a visual highlight around an element in the browser."""
        js_code = f"""
            (function() {{
                const el = document.querySelector({json.dumps(selector)});
                if (el) {{
                    el.style.outline = '4px solid {color}';
                    el.style.boxShadow = '0 0 20px {color}';
                    el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }})();
        """
        await self._crawler.arun(
            url="raw:",
            config=CrawlerRunConfig(
                js_code=js_code,
                session_id=self._session_id,
            ),
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
            "browser_profile_dir": (
                self._credentials.effective_browser_profile_dir
                if self._credentials
                else None
            ),
            "required_secret_keys": (
                self._credentials.required_secret_keys if self._credentials else []
            ),
        }


class C4AIMotorProvider:
    """Opens Crawl4AI browser sessions for AriadneSession.

    Supports three auth strategies:
    - persistent_profile: Uses a persistent browser profile directory
    - env_secrets: Performs direct login with env-resolved credentials
    - mixed: Attempts persistent profile first, falls back to env-secrets login

    Usage::

        motor = C4AIMotorProvider()
        session = AriadneSession("linkedin")
        meta = await session.run(motor, job_id="123", cv_path=Path("cv.pdf"))
    """

    @asynccontextmanager
    async def open_session(
        self,
        session_id: str,
        credentials: ResolvedPortalCredentials | None = None,
        visible: bool = False,
    ) -> AsyncIterator[C4AIMotorSession]:
        """Open a Crawl4AI browser session.

        Args:
            session_id: Unique session name (used for tab/CDP reuse).
            credentials: Optional runtime credential metadata for the session.
                When auth_strategy is env_secrets or mixed, login is bootstrapped
                using resolved environment-variable secrets.
            visible: Whether to open a visible browser page.

        Yields:
            C4AIMotorSession ready to observe and execute steps.
        """
        browser_config = self._browser_config(
            credentials=credentials,
            headless=not visible,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            if credentials and credentials.auth_strategy in ("env_secrets", "mixed"):
                await self._bootstrap_env_secret_login(crawler, credentials)

            yield C4AIMotorSession(
                crawler,
                session_id,
                C4AIReplayer(),
                credentials=credentials,
            )

    def _browser_config(
        self,
        credentials: ResolvedPortalCredentials | None,
        headless: bool = True,
    ) -> BrowserConfig:
        if credentials and credentials.effective_browser_profile_dir:
            user_data_dir = str(
                Path(credentials.effective_browser_profile_dir).expanduser().resolve()
            )
            return BrowserConfig(
                browser_type="chromium",
                headless=headless,
                user_data_dir=user_data_dir,
            )

        from src.automation.motors.crawl4ai.browser_config import (
            get_browseros_injected_config,
        )

        return get_browseros_injected_config(headless=headless)

    async def _bootstrap_env_secret_login(
        self,
        crawler: AsyncWebCrawler,
        credentials: ResolvedPortalCredentials,
    ) -> None:
        """Bootstrap login using env-resolved credentials.

        Navigates to the portal login URL and fills common username/password
        selectors with values resolved from environment variables.
        Skips silently if required secrets are not set.
        """
        missing = credentials.missing_required_secrets()
        if missing:
            logger.warning(
                "%s Env-secret login skipped for %s: missing required secrets: %s",
                LogTag.WARN,
                credentials.portal_name,
                missing,
            )
            return

        login_url = credentials.setup_url(
            default_url=f"https://{credentials.matched_domain}/login"
        )
        logger.info(
            "%s Bootstrapping env-secret login for %s at %s",
            LogTag.FAST,
            credentials.portal_name,
            login_url,
        )

        await crawler.arun(
            url=login_url,
            config=CrawlerRunConfig(cache_mode=False),
        )

        username_value = credentials.get_secret("username")
        password_value = credentials.get_secret("password")
        email_value = credentials.get_secret("email")

        steps = []
        if username_value:
            steps.extend(
                [
                    (
                        'input[name*="user"], input[name*="login"], input[name*="email"], input[type="email"]',
                        username_value,
                    ),
                ]
            )
        if email_value:
            steps.append(
                (
                    'input[name*="user"], input[name*="email"], input[type="email"]',
                    email_value,
                )
            )
        if password_value:
            steps.append(
                ('input[name*="pass"], input[type="password"]', password_value)
            )

        if not steps:
            logger.warning(
                "%s Env-secret login skipped for %s: no username/password secrets resolved",
                LogTag.WARN,
                credentials.portal_name,
            )
            return

        username_selector = "input[name*='user'], input[name*='login'], input[name*='email'], input[type='email']"
        password_selector = "input[name*='pass'], input[type='password']"
        submit_selector = "button[type='submit'], input[type='submit']"

        if username_value:
            script = f'SET `{username_selector}` "{username_value}"'
            await crawler.arun(
                url=login_url,
                config=CrawlerRunConfig(
                    c4a_script=script, session_id=crawler.session_id
                ),
            )

        if password_value:
            script = f'SET `{password_selector}` "{password_value}"'
            await crawler.arun(
                url=login_url,
                config=CrawlerRunConfig(
                    c4a_script=script, session_id=crawler.session_id
                ),
            )

        script = f"CLICK `{submit_selector}`"
        result = await crawler.arun(
            url=login_url,
            config=CrawlerRunConfig(c4a_script=script, session_id=crawler.session_id),
        )

        if result.success:
            logger.info(
                "%s Env-secret login submitted for %s",
                LogTag.OK,
                credentials.portal_name,
            )
        else:
            logger.warning(
                "%s Env-secret login submission failed for %s: %s",
                LogTag.WARN,
                credentials.portal_name,
                result.error_message,
            )

    async def run_agent(
        self,
        portal: str,
        url: str,
        context: dict[str, Any],
        session_id: str | None = None,
    ) -> Any:
        """Crawl4AI does not yet support Level 2 agentic discovery."""
        raise NotImplementedError("Crawl4AI does not yet support Level 2 discovery.")
