"""OS-Native Tools Motor Provider — Conceptual stub for native automation.

Implements the Ariadne Motor Protocol for OS-level tool calls.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from src.automation.ariadne.danger_contracts import ApplyDangerReport, ApplyDangerSignals
from src.automation.ariadne.danger_detection import ApplyDangerDetector
from src.automation.ariadne.models import AriadneStep
from src.automation.credentials import ResolvedPortalCredentials

logger = logging.getLogger(__name__)


class OSNativeMotorSession:
    """Conceptual single-session interface for OS-level tools.

    Currently unimplemented. Asserts that this is a planned future motor.
    """

    def __init__(self, credentials: ResolvedPortalCredentials | None = None) -> None:
        self._credentials = credentials
        self._danger_detector = ApplyDangerDetector()

    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        """Verify native UI presence.

        Args:
            selectors: Native tool or system UI selectors.

        Raises:
            NotImplementedError: OS-Native motor is not yet implemented.
        """
        raise NotImplementedError(
            "OS-Native motor is conceptual and not yet implemented."
        )

    async def execute_step(
        self,
        step: AriadneStep,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        is_first: bool,
        url: str | None,
    ) -> None:
        """Execute a native UI interaction.

        Raises:
            NotImplementedError: OS-Native motor is not yet implemented.
        """
        raise NotImplementedError(
            "OS-Native motor is conceptual and not yet implemented."
        )

    async def inspect_danger(self, application_url: str | None) -> ApplyDangerReport:
        """Inspect OS state for safety risks."""
        # Return a safe default for now, as we can't actually inspect anything.
        return self._danger_detector.detect(
            ApplyDangerSignals(
                dom_text="OS-Native motor is conceptual",
                current_url=application_url,
                application_url=application_url,
            )
        )

    async def begin_human_intervention(
        self,
        artifact_dir: Path,
        step: AriadneStep,
        reason: str,
    ) -> dict[str, Any]:
        """Stop OS-native automation for operator help.

        Raises:
            NotImplementedError: OS-Native motor is not yet implemented.
        """
        raise NotImplementedError(
            "OS-Native motor is conceptual and not yet implemented."
        )


class OSNativeMotorProvider:
    """Factory for opening OS-native tool sessions.

    Conceptual stub for future desktop automation.
    """

    @asynccontextmanager
    async def open_session(
        self,
        session_id: str,
        credentials: ResolvedPortalCredentials | None = None,
    ) -> AsyncIterator[OSNativeMotorSession]:
        """Open an OS-level session context.

        Args:
            session_id: Session identifier.
            credentials: Optional runtime credentials.

        Yields:
            OSNativeMotorSession (currently unimplemented).
        """
        yield OSNativeMotorSession(credentials=credentials)
