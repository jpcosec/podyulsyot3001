"""Async bridge between the Textual event loop and LangGraph/MatchArtifactStore.

All blocking I/O (disk reads, LangGraph invocations) is isolated here so the
Textual UI stays responsive. Callers use ``MatchBus`` from a Textual worker or
async context; the returned data types are the canonical contracts from
``src.match_skill.contracts``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.match_skill.contracts import ReviewPayload, ReviewSurface
from src.match_skill.storage import MatchArtifactStore


class MatchBus:
    """Async bridge exposing artifact reads and graph resume actions.

    This class purposely contains no Textual imports so it can be tested in
    isolation without a running Textual application.

    Args:
        store: MatchArtifactStore instance used for disk I/O.
        app: Compiled LangGraph app used for resume operations.
        config: LangGraph invocation config (must contain ``configurable.thread_id``).
    """

    def __init__(
        self,
        *,
        store: MatchArtifactStore,
        app: Any,
        config: dict[str, Any],
    ) -> None:
        self.store = store
        self.app = app
        self.config = config

    # ------------------------------------------------------------------
    # Artifact reads (sync wrappers - called from Textual workers)
    # ------------------------------------------------------------------

    def load_current_review_surface(
        self, source: str, job_id: str
    ) -> ReviewSurface:
        """Load the current review surface payload from disk.

        Args:
            source: Source identifier (e.g. CV source name).
            job_id: Job identifier.

        Returns:
            Parsed ``ReviewSurface`` ready for display.

        Raises:
            FileNotFoundError: If no review surface exists for the given job.
        """
        path = (
            self.store.job_root(source, job_id) / "review" / "current.json"
        )
        if not path.exists():
            raise FileNotFoundError(
                f"No review surface found at {path}. "
                "Run the match skill first to generate a proposal."
            )
        raw = self.store.load_json(path)
        return ReviewSurface.model_validate(raw)

    # ------------------------------------------------------------------
    # LangGraph actions (sync wrappers - called from Textual workers)
    # ------------------------------------------------------------------

    def resume_with_review(self, review_payload: ReviewPayload) -> dict[str, Any]:
        """Resume the paused LangGraph thread with a structured review payload.

        Args:
            review_payload: Validated ``ReviewPayload`` built by the UI layer.

        Returns:
            Final graph state dict after resumption.
        """
        self.app.update_state(
            self.config,
            {"review_payload": review_payload.model_dump()},
            as_node="human_review_node",
        )
        return self.app.invoke(None, config=self.config)
