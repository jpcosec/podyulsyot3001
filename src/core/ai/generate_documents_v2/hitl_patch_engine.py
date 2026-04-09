"""Deterministic patch application engine for HITL nodes.

Each HITL node calls ``apply_patches`` when the graph resumes after an
interrupt.  The engine reads ``pending_patches`` from state, applies each
``GraphPatch`` in order, persists the applied bundle, and clears the field
so downstream nodes see a clean slate.
"""

from __future__ import annotations

import logging
from typing import Any

from src.core.ai.generate_documents_v2.contracts.hitl import (
    GraphPatch,
    PatchBundle,
    ProfileUpdateRecord,
)
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Outcome constants (mirrors the LangGraph routing keys)
# ---------------------------------------------------------------------------

OUTCOME_APPROVED = "approved"
OUTCOME_REJECTED = "rejected"
OUTCOME_REGENERATING = "regenerating"


def apply_patches(
    *,
    state: dict[str, Any],
    stage: str,
    outcome_key: str,
    mutable_state_key: str,
    store: PipelineArtifactStore,
) -> dict[str, Any]:
    """Apply ``pending_patches`` from *state* for the given HITL *stage*.

    Args:
        state: Current pipeline state dict (read-only input).
        stage: HITL stage name used for artifact persistence and logging
            (e.g. ``"hitl_1_match_evidence"``).
        outcome_key: State key that controls downstream routing
            (e.g. ``"match_outcome"``).
        mutable_state_key: Top-level state key whose dict value patches with
            ``action="modify"`` target (e.g. ``"matches"``, ``"blueprint"``).
        store: Artifact store used to persist the applied patch bundle.

    Returns:
        A partial state dict to merge into the graph state.  Always contains
        ``pending_patches: []`` (cleared) and the resolved *outcome_key*.
    """
    raw_patches: list[dict[str, Any]] = state.get("pending_patches") or []
    patches = [GraphPatch.model_validate(p) for p in raw_patches]

    outcome = OUTCOME_APPROVED
    updated_artifact: Any = state.get(mutable_state_key)
    profile_updates: list[dict[str, Any]] = []

    for patch in patches:
        outcome, updated_artifact = _apply_one(
            patch=patch,
            current_outcome=outcome,
            artifact=updated_artifact,
            stage=stage,
        )
        if patch.persist_to_profile and patch.action == "modify":
            record = ProfileUpdateRecord(
                field_path=patch.target_id,
                old_value=None,
                new_value=patch.new_value,
                source_stage=stage,
                approved=False,
            )
            profile_updates.append(record.model_dump())

    _persist_bundle(
        store=store,
        source=state["source"],
        job_id=state["job_id"],
        stage=stage,
        patches=patches,
    )

    existing_updates: list[dict[str, Any]] = list(
        state.get("pending_profile_updates") or []
    )
    result: dict[str, Any] = {
        "pending_patches": [],
        outcome_key: outcome,
        "status": "running" if outcome != OUTCOME_REJECTED else "rejected",
        "pending_profile_updates": existing_updates + profile_updates,
    }
    if updated_artifact is not state.get(mutable_state_key):
        result[mutable_state_key] = updated_artifact

    logger.info(
        "%s %s: applied %d patch(es) → outcome=%s, profile_updates=%d",
        LogTag.OK,
        stage,
        len(patches),
        outcome,
        len(profile_updates),
    )
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _apply_one(
    *,
    patch: GraphPatch,
    current_outcome: str,
    artifact: Any,
    stage: str,
) -> tuple[str, Any]:
    """Return (new_outcome, updated_artifact) for a single patch."""
    action = patch.action

    if action == "approve":
        return OUTCOME_APPROVED, artifact

    if action == "reject":
        logger.info(
            "%s %s: patch rejected field=%s", LogTag.WARN, stage, patch.target_id
        )
        return OUTCOME_REJECTED, artifact

    if action == "request_regeneration":
        logger.info(
            "%s %s: regeneration requested for field=%s",
            LogTag.WARN,
            stage,
            patch.target_id,
        )
        return OUTCOME_REGENERATING, artifact

    if action == "modify":
        updated = _apply_modify(artifact=artifact, patch=patch, stage=stage)
        return current_outcome, updated

    # move_to_doc and any future actions: treat as approve
    return current_outcome, artifact


def _apply_modify(*, artifact: Any, patch: GraphPatch, stage: str) -> Any:
    """Apply a modify patch to *artifact* and return the updated value.

    If *artifact* is a dict the patch targets ``artifact[target_id]``.
    If *artifact* is a list the patch targets the first element whose
    ``id`` (or ``target_id``) matches ``patch.target_id``.
    """
    if isinstance(artifact, dict):
        updated = dict(artifact)
        updated[patch.target_id] = patch.new_value
        logger.info("%s %s: modified dict key=%s", LogTag.OK, stage, patch.target_id)
        return updated

    if isinstance(artifact, list):
        updated_list = []
        matched = False
        for item in artifact:
            if isinstance(item, dict) and (
                item.get("id") == patch.target_id
                or item.get("target_id") == patch.target_id
            ):
                item = dict(item)
                item["value"] = patch.new_value
                matched = True
            updated_list.append(item)
        if not matched:
            logger.warning(
                "%s %s: modify target_id=%s not found in list",
                LogTag.WARN,
                stage,
                patch.target_id,
            )
        return updated_list

    logger.warning(
        "%s %s: modify on unsupported artifact type=%s",
        LogTag.WARN,
        stage,
        type(artifact).__name__,
    )
    return artifact


def _persist_bundle(
    *,
    store: PipelineArtifactStore,
    source: str,
    job_id: str,
    stage: str,
    patches: list[GraphPatch],
) -> None:
    bundle = PatchBundle(stage=stage, patches=patches)
    store.write_stage(
        source=source,
        job_id=job_id,
        stage=f"{stage}/applied_patches",
        payload=bundle.model_dump(),
    )


# ---------------------------------------------------------------------------
# Dot-path helper — used by profile_updater node
# ---------------------------------------------------------------------------


def _apply_dot_path(obj: dict, path: str, value: Any) -> dict:
    """Return a shallow-copied *obj* with *value* set at the dot-separated *path*.

    Intermediate dicts are created as needed.  Only the dicts along the path
    are copied; other branches are shared.

    Examples::

        _apply_dot_path({}, "skills.languages", ["en", "de"])
        # → {"skills": {"languages": ["en", "de"]}}

        _apply_dot_path({"a": 1}, "b", 2)
        # → {"a": 1, "b": 2}
    """
    keys = path.split(".")
    result = dict(obj)
    current = result
    for key in keys[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
        current[key] = dict(child)
        current = current[key]
    current[keys[-1]] = value
    return result
