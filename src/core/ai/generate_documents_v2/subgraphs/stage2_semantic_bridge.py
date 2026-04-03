"""Stage 2 — Semantic Bridge: ProfileKG + JobKG → MatchEdges."""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, START, StateGraph

from src.core.ai.generate_documents_v2.contracts.profile import ProfileKG
from src.core.ai.generate_documents_v2.contracts.job import JobKG
from src.core.ai.generate_documents_v2.state import GenerateDocumentsV2State
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


def build_stage2_semantic_bridge(store: PipelineArtifactStore) -> Any:
    """Build the Stage 2 subgraph."""
    workflow = StateGraph(GenerateDocumentsV2State)
    workflow.add_node("alignment_engine", _make_alignment_node(store))
    workflow.add_node("hitl_1_match_evidence", _make_hitl1_node())
    workflow.add_edge(START, "alignment_engine")

    def _route_to_hitl(state: GenerateDocumentsV2State) -> str:
        if state.get("auto_approve_review", False):
            return "approved"
        return "hitl"

    workflow.add_conditional_edges(
        "alignment_engine",
        _route_to_hitl,
        {"approved": END, "hitl": "hitl_1_match_evidence"},
    )
    workflow.add_conditional_edges(
        "hitl_1_match_evidence",
        lambda s: s.get("match_outcome", "approved"),
        {"regenerating": "alignment_engine", "approved": END, "rejected": END},
    )
    return workflow.compile(interrupt_before=["hitl_1_match_evidence"])


def _make_alignment_node(store: PipelineArtifactStore):
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        profile_kg = ProfileKG.model_validate(state["profile_kg"])
        job_kg = JobKG.model_validate(state["job_kg"])
        
        from src.core.ai.generate_documents_v2.nodes.alignment import run_alignment, build_alignment_chain
        
        result = run_alignment(
            source=state["source"],
            job_id=state["job_id"],
            profile_kg=profile_kg,
            job_kg=job_kg,
            chain=build_alignment_chain(),
            store=store,
        )
        return result
    return node


def _make_hitl1_node():
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        if state.get("auto_approve_review", False):
            return {"match_outcome": "approved", "status": "running"}
        return {"status": "interrupted"}
    return node
