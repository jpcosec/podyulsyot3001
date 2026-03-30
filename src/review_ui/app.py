"""Main Textual application for the match skill HITL review TUI.

Launch via the unified CLI::

    python -m src.cli.main review --source <source> --job-id <job_id>

Or programmatically::

    from src.review_ui.app import MatchReviewApp
    app = MatchReviewApp(bus=bus, source=source, job_id=job_id)
    app.run()
"""

from __future__ import annotations

from typing import Any, Optional

from textual.app import App, ComposeResult

from src.review_ui.bus import MatchBus
from src.review_ui.screens.review_screen import ReviewScreen


class MatchReviewApp(App):
    """Textual application for reviewing a match proposal and submitting decisions.

    Args:
        bus: Pre-configured ``MatchBus`` connecting to LangGraph + disk artifacts.
        source: Source identifier (e.g. CV source name) used to locate artifacts.
        job_id: Job identifier used to locate artifacts.
    """

    TITLE = "Match Skill · HITL Review"
    SUB_TITLE = "Human-in-the-loop review gate"

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(
        self,
        *,
        bus: MatchBus,
        source: Optional[str] = None,
        job_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._bus = bus
        self._source = source
        self._job_id = job_id

    def compose(self) -> ComposeResult:
        """Yield the initial screen as the root widget."""
        return iter([])  # Screens are pushed in `on_mount`

    def on_mount(self) -> None:
        """Push the appropriate screen once the app event loop is running."""
        from src.review_ui.screens.explorer_screen import JobExplorerScreen
        from src.review_ui.screens.review_screen import ReviewScreen

        if self._source and self._job_id:
            # Direct access mode
            self.push_screen(
                ReviewScreen(
                    bus=self._bus,
                    source=self._source,
                    job_id=self._job_id,
                )
            )
        else:
            # Explorer mode
            self.push_screen(
                JobExplorerScreen(bus=self._bus)
            )
