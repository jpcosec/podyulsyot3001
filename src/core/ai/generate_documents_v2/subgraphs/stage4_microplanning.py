"""Stage 4 — Microplanning: GlobalBlueprint → DraftedDocuments."""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, START, StateGraph

from src.core.ai.generate_documents_v2.contracts.blueprint import GlobalBlueprint
from src.core.ai.generate_documents_v2.state import GenerateDocumentsV2State
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


def build_stage4_microplanning(store: PipelineArtifactStore) -> Any:
    """Build the Stage 4 subgraph."""
    workflow = StateGraph(GenerateDocumentsV2State)
    workflow.add_node("redaction_smoothing", _make_drafting_node(store))
    workflow.add_edge(START, "redaction_smoothing")
    workflow.add_edge("redaction_smoothing", END)
    return workflow.compile()


def _make_drafting_node(store: PipelineArtifactStore):
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        blueprint = GlobalBlueprint.model_validate(state["blueprint"])
        
        from src.core.ai.generate_documents_v2.nodes.drafting import run_drafting, build_drafting_chain
        chain = build_drafting_chain()
        
        # Run drafting for all 3 doc types
        results = {}
        for doc_type in ["cv", "letter", "email"]:
            res = run_drafting(
                source=state["source"],
                job_id=state["job_id"],
                doc_type=doc_type,
                blueprint=blueprint,
                chain=chain,
                store=store,
            )
            results[f"{doc_type}_document"] = res["drafted_document"]
            
        results["status"] = "drafted"
        return results
    return node
