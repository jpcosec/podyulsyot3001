"""State definition for the generate_documents_v2 pipeline."""

from __future__ import annotations

from typing import Any, TypedDict


class GenerateDocumentsV2State(TypedDict, total=False):
    """Full state for the generate_documents_v2 pipeline."""

    # Primary inputs (Stage 0)
    source: str
    job_id: str
    source_url: str | None
    profile_path: str | None
    mapping_path: str | None
    target_language: str
    auto_approve_review: bool

    # Direct data injection (optional overrides for path-based loading)
    profile_evidence: dict[str, Any]
    requirements: list[dict[str, Any]]

    # Data plane artifacts (P1-P5)
    profile_data: dict[str, Any]
    profile_kg: dict[str, Any]
    section_mapping: list[dict[str, Any]]
    job_kg: dict[str, Any]
    job_delta: dict[str, Any]
    matches: list[dict[str, Any]]
    blueprint: dict[str, Any]
    cv_document: dict[str, Any]
    letter_document: dict[str, Any]
    email_document: dict[str, Any]
    markdown_bundle: dict[str, Any]

    # Flow control
    status: str
    current_node: str
    artifact_refs: dict[str, str]
    error_state: dict[str, Any] | None

    # HITL outcomes (approved / rejected / regenerating)
    match_outcome: str
    blueprint_outcome: str
    bundle_outcome: str
