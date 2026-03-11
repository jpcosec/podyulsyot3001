"""Control-plane graph state contract.

Graph state carries routing and execution metadata only.
Business payload artifacts live in the Data Plane on disk.
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

FailureType = Literal[
    "MODEL_FAILURE",
    "TOOL_FAILURE",
    "IO_FAILURE",
    "INPUT_MISSING",
    "SCHEMA_INVALID",
    "POLICY_VIOLATION",
    "PARSER_REJECTED",
    "REVIEW_LOCK_MISSING",
    "INTERNAL_ERROR",
]

RunStatus = Literal["running", "pending_review", "failed", "completed"]
ReviewDecision = Literal["approve", "request_regeneration", "reject"]


class ErrorContext(TypedDict):
    failure_type: FailureType
    message: str
    attempt_count: int


class ArtifactRefs(TypedDict):
    """Lightweight pointers to Data Plane artifacts relevant to current routing."""

    last_proposed_state_ref: NotRequired[str]
    last_decision_ref: NotRequired[str]
    emergent_evidence_patch_ref: NotRequired[str]
    active_feedback_ref: NotRequired[str]


class GraphState(TypedDict):
    """Single source of truth for control-plane execution context."""

    source: str
    job_id: str
    run_id: str
    source_url: NotRequired[str]

    current_node: str
    status: RunStatus

    review_decision: NotRequired[ReviewDecision | None]
    pending_gate: NotRequired[str | None]

    ingested_data: NotRequired[dict[str, Any]]
    extracted_data: NotRequired[dict[str, Any]]
    matched_data: NotRequired[dict[str, Any]]
    my_profile_evidence: NotRequired[list[dict[str, Any]]]
    last_decision: NotRequired[dict[str, Any]]
    active_feedback: NotRequired[list[dict[str, Any]]]

    error_state: NotRequired[ErrorContext | None]
    artifact_refs: NotRequired[ArtifactRefs]


def build_thread_id(source: str, job_id: str) -> str:
    """Canonical checkpoint identity for LangGraph runs."""
    return f"{source}_{job_id}"
