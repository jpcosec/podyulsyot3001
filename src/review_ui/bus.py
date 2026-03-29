"""Async bridge between the Textual event loop and the LangGraph API.

All state mutations must go through the LangGraph API so the server remains the
single source of truth for checkpoints and thread state.
"""

from __future__ import annotations

import asyncio
from typing import Any

from src.ai.match_skill.contracts import ReviewPayload, ReviewSurface
from src.ai.match_skill.storage import MatchArtifactStore
from src.core.api_client import LangGraphAPIClient
import logging

from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class MatchBus:
    """Async bridge exposing artifact reads and graph resume actions.

    Args:
        store: MatchArtifactStore instance used for disk I/O.
        client: LangGraphAPIClient used for all stateful graph interactions.
        config: LangGraph invocation config (must contain ``configurable.thread_id``).
    """

    def __init__(
        self,
        *,
        store: MatchArtifactStore,
        client: LangGraphAPIClient,
        config: dict[str, Any],
    ) -> None:
        self.store = store
        self.client = client
        self.config = config

    # ------------------------------------------------------------------
    # Artifact reads (sync wrappers - called from Textual workers)
    # ------------------------------------------------------------------

    def load_current_review_surface(self, source: str, job_id: str) -> ReviewSurface:
        """Load the current review surface payload from disk."""
        path = self.store.job_root(source, job_id) / "review" / "current.json"
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

        Uses the LangGraph API as the only stateful control plane.
        """
        thread_id = self.config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id missing in config for remote resume")

        logger.info(f"{LogTag.OK} Resuming remote thread {thread_id} via API")
        loop = asyncio.new_event_loop()
        try:
            payload = {"review_payload": review_payload.model_dump()}
            return loop.run_until_complete(
                self.client.resume_thread(thread_id, payload)
            )
        finally:
            loop.close()
