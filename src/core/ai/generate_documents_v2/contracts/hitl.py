"""Review and patch contracts for generate_documents_v2 interruptions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

PatchAction = Literal[
    "approve",
    "reject",
    "modify",
    "request_regeneration",
    "move_to_doc",
]


class GraphPatch(BaseModel):
    """One operator action applied to a reviewable graph artifact."""

    action: PatchAction
    target_id: str
    new_value: Any | None = None
    feedback_note: str = ""
    persist_to_profile: bool = False
    target_stage: str | None = None
    target_type: str | None = None


# ---------------------------------------------------------------------------
# Review payloads — what the reviewer sees at each checkpoint
# ---------------------------------------------------------------------------


class MatchReviewPayload(BaseModel):
    """Artifact surface presented to the reviewer at hitl_1_match_evidence."""

    stage: str = "hitl_1_match_evidence"
    job_id: str
    matches: list[dict[str, Any]]
    job_delta: dict[str, Any]


class BlueprintReviewPayload(BaseModel):
    """Artifact surface presented to the reviewer at hitl_2_blueprint_logic."""

    stage: str = "hitl_2_blueprint_logic"
    job_id: str
    blueprint: dict[str, Any]


class BundleReviewPayload(BaseModel):
    """Artifact surface presented to the reviewer at hitl_3_content_style."""

    stage: str = "hitl_3_content_style"
    job_id: str
    markdown_bundle: dict[str, Any]


# ---------------------------------------------------------------------------
# PatchBundle — ordered list of patches applied to one stage
# ---------------------------------------------------------------------------


class PatchBundle(BaseModel):
    """Collection of patches applied during a single HITL stage."""

    stage: str
    patches: list[GraphPatch]


# ---------------------------------------------------------------------------
# ProfileUpdateRecord — durable profile change derived from a review patch
# ---------------------------------------------------------------------------


class ProfileUpdateRecord(BaseModel):
    """A single durable profile change derived from a review patch."""

    field_path: str          # dot-separated path into the profile JSON, e.g. "skills.languages"
    old_value: Any | None    # what was there before (for auditability)
    new_value: Any            # the replacement value
    source_stage: str         # which HITL stage generated this
    approved: bool = False    # must be explicitly approved before writing
