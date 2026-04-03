"""Stage 3 — Macroplanning: Section Strategy + JobDelta + MatchEdges → GlobalBlueprint."""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, START, StateGraph

from src.core.ai.generate_documents_v2.contracts.job import JobDelta, JobKG
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.contracts.profile import SectionMappingItem
from src.core.ai.generate_documents_v2.state import GenerateDocumentsV2State
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


def build_stage3_macroplanning(store: PipelineArtifactStore) -> Any:
    """Build the Stage 3 subgraph."""
    workflow = StateGraph(GenerateDocumentsV2State)
    workflow.add_node("conciliator", _make_blueprint_node(store))
    workflow.add_node("hitl_2_blueprint_logic", _make_hitl2_node())
    workflow.add_edge(START, "conciliator")

    def _route_to_hitl(state: GenerateDocumentsV2State) -> str:
        if state.get("auto_approve_review", False):
            return "approved"
        return "hitl"

    workflow.add_conditional_edges(
        "conciliator",
        _route_to_hitl,
        {"approved": END, "hitl": "hitl_2_blueprint_logic"},
    )
    workflow.add_conditional_edges(
        "hitl_2_blueprint_logic",
        lambda s: s.get("blueprint_outcome", "approved"),
        {"regenerating": "conciliator", "approved": END, "rejected": END},
    )
    return workflow.compile(interrupt_before=["hitl_2_blueprint_logic"])


def _make_blueprint_node(store: PipelineArtifactStore):
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        mapping = [SectionMappingItem.model_validate(m) for m in state["section_mapping"]]
        job_delta = JobDelta.model_validate(state["job_delta"])
        matches = [MatchEdge.model_validate(m) for m in state["matches"]]
        job_kg = JobKG.model_validate(state["job_kg"]) if state.get("job_kg") else None
        
        from src.core.ai.generate_documents_v2.nodes.blueprint import run_blueprint, build_blueprint_chain
        
        result = run_blueprint(
            source=state["source"],
            job_id=state["job_id"],
            application_id=f"{state['source']}-{state['job_id']}",
            strategy_type="professional",
            section_mapping=mapping,
            job_delta=job_delta,
            matches=matches,
            chain=build_blueprint_chain(),
            store=store,
            job_kg=job_kg,
        )
        return result
    return node


def _make_hitl2_node():
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        if state.get("auto_approve_review", False):
            return {"blueprint_outcome": "approved", "status": "running"}
        return {"status": "interrupted"}
    return node
