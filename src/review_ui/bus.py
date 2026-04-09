"""Async bridge between the Textual event loop and the LangGraph API."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from src.core.ai.generate_documents_v2.contracts.hitl import GraphPatch
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.core.api_client import LangGraphAPIClient
import logging

from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)

_REVIEW_STAGE_MAP = {
    "hitl_1_match_evidence": ("match_edges", "Match Evidence Review"),
    "hitl_2_blueprint_logic": ("blueprint", "Blueprint Review"),
    "hitl_3_content_style": ("markdown_bundle", "Content And Style Review"),
    "stage_2_semantic_bridge": ("match_edges", "Match Evidence Review"),
    "stage_3_macroplanning": ("blueprint", "Blueprint Review"),
    "stage_5_assembly_render": ("markdown_bundle", "Content And Style Review"),
    "hitl_4_profile_updates": ("profile_updater", "Profile Update Review"),
}


@dataclass
class ReviewSurfaceData:
    """Resolved review checkpoint payload for the Textual UI."""

    stage: str
    title: str
    artifact_stage: str
    payload: dict[str, Any]

    def pretty_json(self) -> str:
        """Return the checkpoint payload as formatted JSON for display."""
        return json.dumps(self.payload, indent=2, ensure_ascii=False)


class MatchBus:
    """Async bridge exposing artifact reads and graph resume actions."""

    def __init__(
        self,
        *,
        store: PipelineArtifactStore,
        client: LangGraphAPIClient,
        config: dict[str, Any],
    ) -> None:
        self.store = store
        self.client = client
        self.config = config

    # ------------------------------------------------------------------
    # Artifact reads (sync wrappers - called from Textual workers)
    # ------------------------------------------------------------------

    def load_current_review_surface(
        self, source: str, job_id: str
    ) -> ReviewSurfaceData:
        """Load the currently pending review checkpoint from disk."""
        stage = self._pending_review_stage()
        artifact_stage, title = _resolve_artifact_stage(stage)
        payload = self.store.load_stage(source, job_id, artifact_stage)
        if payload is None:
            raise FileNotFoundError(
                f"No review payload found for {source}/{job_id} at stage {artifact_stage}."
            )
        return ReviewSurfaceData(
            stage=stage,
            title=title,
            artifact_stage=artifact_stage,
            payload=payload,
        )

    # ------------------------------------------------------------------
    # LangGraph actions (sync wrappers - called from Textual workers)
    # ------------------------------------------------------------------

    def resume_with_review(self, action: str) -> dict[str, Any]:
        """Resume the paused LangGraph thread with a simple review action."""
        thread_id = self.config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id missing in config for remote resume")

        stage = self._pending_review_stage()
        patch = GraphPatch(action=action, target_id="__review__")
        client = LangGraphAPIClient(self.client.url)

        logger.info(f"{LogTag.OK} Resuming remote thread {thread_id} via API")
        loop = asyncio.new_event_loop()
        try:
            payload = {"pending_patches": [patch.model_dump()]}
            return loop.run_until_complete(
                client.resume_thread(thread_id, payload, node_name=stage)
            )
        finally:
            loop.close()

    def _pending_review_stage(self) -> str:
        """Return the currently pending HITL node for the configured thread."""
        thread_id = self.config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id missing in config for remote review")

        client = LangGraphAPIClient(self.client.url)

        loop = asyncio.new_event_loop()
        try:
            state = loop.run_until_complete(
                client.client.threads.get_state(thread_id, subgraphs=True)
            )
        finally:
            loop.close()

        next_nodes = state.get("next", [])
        for node in next_nodes:
            if node in _REVIEW_STAGE_MAP:
                return node
        raise ValueError(
            f"Thread {thread_id} is not waiting at a supported review stage"
        )


def _resolve_artifact_stage(stage: str) -> tuple[str, str]:
    """Map a HITL node name to the persisted artifact directory and UI title."""
    if stage not in _REVIEW_STAGE_MAP:
        raise ValueError(f"Unsupported review stage: {stage}")
    return _REVIEW_STAGE_MAP[stage]
