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

# Legacy aliases for backward compatibility with older threads
_LEGACY_REVIEW_STAGES = {
    "stage_2_semantic_bridge": ("match_edges", "Match Evidence Review"),
    "stage_3_macroplanning": ("blueprint", "Blueprint Review"),
    "stage_5_assembly_render": ("markdown_bundle", "Content And Style Review"),
}

_REVIEW_STAGE_MAP = {
    "hitl_1_match_evidence": ("match_edges", "Match Evidence Review"),
    "hitl_2_blueprint_logic": ("blueprint", "Blueprint Review"),
    "hitl_3_content_style": ("markdown_bundle", "Content And Style Review"),
    "hitl_4_profile_updates": ("profile_updater", "Profile Update Review"),
    **_LEGACY_REVIEW_STAGES,
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

        if artifact_stage == "match_edges":
            job_kg = self.store.load_stage(source, job_id, "job_kg")
            job_delta = self.store.load_stage(source, job_id, "job_delta")
            if job_kg:
                payload["job_kg"] = job_kg
            if job_delta:
                payload["job_delta"] = job_delta

        return ReviewSurfaceData(
            stage=stage,
            title=title,
            artifact_stage=artifact_stage,
            payload=payload,
        )

    # ------------------------------------------------------------------
    # LangGraph actions (sync wrappers - called from Textual workers)
    # ------------------------------------------------------------------

    def resume_with_review(
        self,
        action: str,
        patches: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Resume the paused LangGraph thread with review action and optional patches.

        Args:
            action: Main action (approve/reject)
            patches: Optional per-match modifications
        """
        thread_id = self.config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id missing in config for remote resume")

        stage = self._pending_review_stage()

        all_patches: list[GraphPatch] = []

        if patches:
            for p in patches:
                all_patches.append(GraphPatch(**p))

        all_patches.append(GraphPatch(action=action, target_id="__review__"))

        logger.info(f"{LogTag.OK} Resuming remote thread {thread_id} via API")
        payload = {"pending_patches": [p.model_dump() for p in all_patches]}
        return asyncio.run(self.client.resume_thread(thread_id, payload, node_name=stage))

    def _pending_review_stage(self) -> str:
        """Return the currently pending HITL node for the configured thread."""
        thread_id = self.config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id missing in config for remote review")

        state = asyncio.run(self.client.client.threads.get_state(thread_id, subgraphs=True))

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
