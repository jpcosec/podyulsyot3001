"""Shared top-level LangGraph state for the schema-v0 pipeline."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

RunStatus = Literal["pending", "running", "pending_review", "completed", "failed"]


class ErrorContext(TypedDict):
    """Serializable error information propagated through the graph."""

    node: str
    message: str
    details: dict[str, Any] | None


class GraphState(TypedDict, total=False):
    """Lightweight control-plane state for the unified schema-v0 pipeline.

    Heavy payloads are persisted under ``data/jobs``. State keeps only routing
    signals, metadata refs, and UI-facing summaries.
    """

    source: str
    source_url: str
    job_id: str
    run_id: str
    current_node: str
    status: RunStatus
    artifact_refs: dict[str, str]
    profile_evidence_ref: str
    auto_approve_review: bool
    requirements: list[dict[str, Any]]
    profile_evidence: list[dict[str, Any]]
    generated_documents_summary: dict[str, Any]
    render_summary: dict[str, Any]
    error_state: ErrorContext | None
