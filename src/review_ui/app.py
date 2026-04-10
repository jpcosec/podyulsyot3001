"""Main Textual application for the generate_documents_v2 HITL review TUI."""

from __future__ import annotations

from typing import Any, Optional, Type

from textual import work
from textual.app import App
from textual.screen import Screen

from src.review_ui.bus import MatchBus


class MatchReviewApp(App):
    """Textual application for reviewing pending generate_documents_v2 checkpoints."""

    TITLE = "Generate Documents V2 · HITL Review"
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

    def on_mount(self) -> None:
        """Push the appropriate screen once the app event loop is running."""
        from src.review_ui.screens.explorer_screen import JobExplorerScreen

        if self._source and self._job_id:
            # Direct access mode - need to resolve stage first
            self._push_stage_screen(self._source, self._job_id)
        else:
            # Explorer mode
            self.push_screen(JobExplorerScreen(bus=self._bus))

    @work(thread=True)
    def _push_stage_screen(self, source: str, job_id: str) -> None:
        """Resolve the pending stage and push the correct screen."""
        try:
            # Update bus config for this thread
            thread_id = f"{source}-{job_id}" # Simplistic, usually handled by client
            # Actually we should let the bus handle it or use the one from list_jobs
            
            # For direct access, we assume we need to find the thread first or use source-job_id
            # The CLI usually passes the right thread_id in config if it knows it.
            
            # Get the stage
            from src.review_ui.screens.match_review_screen import MatchReviewScreen
            from src.review_ui.screens.blueprint_review_screen import BlueprintReviewScreen
            from src.review_ui.screens.content_review_screen import ContentReviewScreen
            from src.review_ui.screens.profile_diff_screen import ProfileDiffScreen

            # MatchBus methods are sync wrappers
            stage = self._bus._pending_review_stage()
            
            screen_class: Type[Screen]
            if stage.startswith("hitl_1") or stage == "stage_2_semantic_bridge":
                screen_class = MatchReviewScreen
            elif stage.startswith("hitl_2") or stage == "stage_3_macroplanning":
                screen_class = BlueprintReviewScreen
            elif stage.startswith("hitl_3") or stage == "stage_5_assembly_render":
                screen_class = ContentReviewScreen
            elif stage.startswith("hitl_4"):
                screen_class = ProfileDiffScreen
            else:
                self.notify(f"Unknown HITL stage: {stage}", severity="error")
                return

            self.app.call_from_thread(
                self.push_screen,
                screen_class(bus=self._bus, source=source, job_id=job_id)
            )
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Routing failed: {e}", severity="error")
            # Fallback to explorer if routing fails
            from src.review_ui.screens.explorer_screen import JobExplorerScreen
            self.app.call_from_thread(self.push_screen, JobExplorerScreen(bus=self._bus))
