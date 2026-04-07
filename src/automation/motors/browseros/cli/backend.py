"""BrowserOS Motor Provider — Browser adapter for Ariadne.

Implements MotorProvider / MotorSession for the BrowserOS backend.
Orchestration (map loading, navigation, run loop) is owned by AriadneSession.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from src.automation.ariadne.contracts import adapt_replay_step
from src.automation.motors.browseros.cli.client import BrowserOSClient
from src.automation.motors.browseros.cli.replayer import BrowserOSReplayer
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class BrowserOSMotorSession:
    """Single-session adapter: observe DOM and execute steps via BrowserOS."""

    def __init__(
        self,
        client: BrowserOSClient,
        page_id: int,
        replayer: BrowserOSReplayer,
    ) -> None:
        self._client = client
        self._page_id = page_id
        self._replayer = replayer

    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        """Check which CSS selectors are present via BrowserOS DOM search.

        Args:
            selectors: CSS selectors to search for on the current page.

        Returns:
            Mapping of selector to presence boolean.
        """
        if not selectors:
            return {}
        results: dict[str, bool] = {}
        for sel in selectors:
            matches = self._client.search_dom(self._page_id, sel)
            results[sel] = bool(matches)
        return results

    async def execute_step(
        self,
        step: Any,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        is_first: bool,
        url: str | None,
    ) -> None:
        """Navigate on first step, then execute the AriadneStep.

        Args:
            step: The semantic step to execute.
            context: Template context used by the replayer.
            cv_path: Local CV path for upload actions.
            letter_path: Optional local cover letter path.
            is_first: Whether this is the first step in the run.
            url: Application URL used for first-step navigation.
        """
        if is_first and url:
            self._client.navigate(url, self._page_id)
        replay_step = adapt_replay_step(step)
        self._replayer.execute_single_step(
            page_id=self._page_id,
            step=replay_step,
            context=context,
            cv_path=cv_path,
            letter_path=letter_path,
        )


class BrowserOSMotorProvider:
    """Opens BrowserOS browser sessions for AriadneSession.

    Usage::

        motor = BrowserOSMotorProvider()
        session = AriadneSession("linkedin")
        meta = await session.run(motor, job_id="123", cv_path=Path("cv.pdf"))
    """

    def __init__(self, client: BrowserOSClient | None = None) -> None:
        self._client = client or BrowserOSClient()

    @asynccontextmanager
    async def open_session(
        self, session_id: str
    ) -> AsyncIterator[BrowserOSMotorSession]:
        """Open a hidden BrowserOS page for the duration of one apply run.

        Args:
            session_id: Unused by BrowserOS (page_id is used instead), kept for protocol compat.

        Yields:
            BrowserOSMotorSession ready to observe and execute steps.
        """
        page_id = self._client.new_hidden_page()
        try:
            yield BrowserOSMotorSession(
                self._client, page_id, BrowserOSReplayer(self._client)
            )
        finally:
            try:
                self._client.close_page(page_id)
            except Exception:
                logger.warning(
                    "%s Failed to close BrowserOS page %s", LogTag.WARN, page_id
                )


def build_browseros_providers(
    portals: list[str] | None = None,
) -> dict[str, BrowserOSMotorProvider]:
    """Build BrowserOS motor providers for a list of portals.

    Each portal gets its own provider instance (separate browser context).
    """
    portals = portals or ["linkedin", "xing", "stepstone"]
    return {portal: BrowserOSMotorProvider() for portal in portals}
