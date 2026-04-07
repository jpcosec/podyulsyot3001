"""Motor Protocol — Contracts between Ariadne and execution motors."""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncContextManager, Protocol, runtime_checkable

from src.automation.ariadne.danger_contracts import ApplyDangerReport
from src.automation.credentials import ResolvedPortalCredentials
from src.automation.ariadne.models import AriadneStep


@runtime_checkable
class MotorSession(Protocol):
    """Single-session interface: observe DOM state and execute one step."""

    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        """Check which CSS selectors are present in the live page.

        Args:
            selectors: CSS selectors to probe.

        Returns:
            Mapping of selector → presence boolean.
        """
        ...

    async def execute_step(
        self,
        step: AriadneStep,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        is_first: bool,
        url: str | None,
    ) -> None:
        """Execute a single AriadneStep on the live page."""
        ...

    async def inspect_danger(self, application_url: str | None) -> ApplyDangerReport:
        """Inspect the live session for risky states and return normalized findings."""
        ...

    async def begin_human_intervention(
        self,
        artifact_dir: Path,
        step: AriadneStep,
        reason: str,
    ) -> dict[str, Any]:
        """Expose the live session to an operator and capture resumable context."""
        ...


@runtime_checkable
class MotorProvider(Protocol):
    """Factory for opening motor sessions."""

    def open_session(
        self,
        session_id: str,
        credentials: ResolvedPortalCredentials | None = None,
    ) -> AsyncContextManager[MotorSession]:
        """Open a browser session scoped to one apply run.

        Args:
            session_id: Unique identifier for this session (used for browser tab/session reuse).
            credentials: Optional runtime credential metadata for the session.

        Returns:
            Async context manager yielding a MotorSession.
        """
        ...
