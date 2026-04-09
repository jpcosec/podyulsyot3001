"""State definition for the generate_documents_v2 pipeline."""

from __future__ import annotations

from typing import Any, TypedDict


class GenerateDocumentsV2State(TypedDict, total=False):
    """Full state for the generate_documents_v2 pipeline.

    ## Stable extension seams (caller-configurable fields)

    The following fields are the primary way to configure pipeline behavior from
    outside the module.  Set them in the initial state dict passed to the graph.

    ``source`` and ``job_id``
        Required.  Identify which ingest artifacts to load.

    ``target_language``
        BCP-47 language tag (e.g. ``"en"``, ``"de"``).  Controls localization in
        the assembly stage and the language suffix on persisted render files.
        Default: ``"en"``.

    ``auto_approve_review``
        When ``True`` the graph skips all three HITL interrupt nodes (match,
        blueprint, bundle) and runs end-to-end without pausing.  Emits a
        ``WARN`` log line at every bypassed checkpoint.
        Default: ``False``.

    ``profile_path``
        Filesystem path to a ``profile_base_data.json`` file.  Overrides the
        default ``data/reference_data/profile/base_profile/profile_base_data.json``.
        Falls back to the ``PROFILE_BASE_DATA_PATH`` environment variable.

    ``mapping_path``
        Filesystem path to a ``section_mapping.json`` file.  Overrides the
        default ``data/reference_data/profile/section_mapping.json``.

    ``profile_evidence``
        Raw profile dict injected directly, bypassing file loading entirely.
        Takes priority over ``profile_path`` when present.

    ``strategy_type``
        Blueprint strategy name forwarded to the LLM macroplanning prompt
        (e.g. ``"professional"``, ``"academic"``).
        Default: ``"professional"``.
        Reserved seam for ``regional_document_strategies``.

    ## Internal pipeline state (not for callers to set)

    All remaining fields are written by pipeline nodes and consumed by
    downstream nodes.  Callers should not pre-populate them.
    """

    # --- Stable caller inputs ---
    source: str
    job_id: str
    source_url: str | None
    profile_path: str | None
    mapping_path: str | None
    target_language: str
    auto_approve_review: bool
    strategy_type: str

    # --- Direct data injection (optional override for path-based loading) ---
    profile_evidence: dict[str, Any]
    requirements: list[dict[str, Any]]

    # --- Data plane artifacts written by nodes (P1-P5) ---
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

    # --- Flow control written by nodes ---
    status: str
    current_node: str
    artifact_refs: dict[str, str]
    error_state: dict[str, Any] | None

    # --- HITL outcomes set by reviewer or auto-approve ---
    match_outcome: str
    blueprint_outcome: str
    bundle_outcome: str

    # --- Caller-settable patch input ---
    # The operator populates this when resuming the graph after an interrupt.
    # Each HITL node reads, applies, and then clears these patches.
    pending_patches: list[dict[str, Any]]

    # --- Profile update accumulator ---
    # Serialized ProfileUpdateRecord items awaiting explicit operator approval.
    pending_profile_updates: list[dict[str, Any]]

    # Serialized ProfileUpdateRecord items that are approved and ready to be
    # written back to the profile JSON. Cleared by profile_updater after writing.
    approved_profile_updates: list[dict[str, Any]]

    # --- Profile writeback review outcome ---
    profile_update_outcome: str
