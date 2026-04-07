"""Stage 5 — Assembly & Render: Drafts → Markdown Bundle → Physical Render."""

from __future__ import annotations

import logging
from typing import Any
from langgraph.graph import END, START, StateGraph

from src.core.ai.generate_documents_v2.contracts.drafting import DraftedDocument
from src.core.ai.generate_documents_v2.contracts.job import JobKG
from src.core.ai.generate_documents_v2.hitl_patch_engine import apply_patches
from src.core.ai.generate_documents_v2.state import GenerateDocumentsV2State
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def build_stage5_assembly_render(store: PipelineArtifactStore) -> Any:
    """Build the Stage 5 subgraph."""
    workflow = StateGraph(GenerateDocumentsV2State)
    workflow.add_node("assembler", _make_assembly_node(store))
    workflow.add_node("hitl_3_content_style", _make_hitl3_node(store))
    workflow.add_edge(START, "assembler")

    def _route_to_hitl(state: GenerateDocumentsV2State) -> str:
        if state.get("auto_approve_review", False):
            return "approved"
        return "hitl"

    workflow.add_conditional_edges(
        "assembler",
        _route_to_hitl,
        {"approved": END, "hitl": "hitl_3_content_style"},
    )
    workflow.add_conditional_edges(
        "hitl_3_content_style",
        lambda s: s.get("bundle_outcome", "approved"),
        {
            "style_regen": END,
            "approved": END,
            "content_regen": END,
            "rejected": END,
        },
    )
    return workflow.compile(interrupt_before=["hitl_3_content_style"])


def _make_assembly_node(store: PipelineArtifactStore):
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        from src.core.ai.generate_documents_v2.nodes.assembly import run_assembly
        
        job_kg = JobKG.model_validate(state["job_kg"])
        
        job_id = state["job_id"]
        result = run_assembly(
            source=state["source"],
            job_id=job_id,
            job_kg=job_kg,
            cv_document=DraftedDocument.model_validate(state["cv_document"]),
            letter_document=DraftedDocument.model_validate(state["letter_document"]),
            email_document=DraftedDocument.model_validate(state["email_document"]),
            profile_data=state["profile_data"],
            target_language=state.get("target_language", "en"),
            store=store,
        )
        return result
    return node


def _make_hitl3_node(store: PipelineArtifactStore):
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        if state.get("auto_approve_review", False):
            logger.warning("%s auto_approve_review=True: skipping HITL review for bundle", LogTag.WARN)
            return {"bundle_outcome": "approved", "status": "running", "pending_patches": []}

        if not state.get("pending_patches"):
            return {"status": "interrupted"}

        return apply_patches(
            state=state,
            stage="hitl_3_content_style",
            outcome_key="bundle_outcome",
            mutable_state_key="markdown_bundle",
            store=store,
        )
    return node
