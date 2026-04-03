"""Stage 1 — Ingestion & Extraction: Job → JobKG → JobDelta."""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, START, StateGraph

from src.core.ai.generate_documents_v2.state import GenerateDocumentsV2State
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore


def build_stage1_ingestion(store: PipelineArtifactStore) -> Any:
    """Build the Stage 1 subgraph."""
    workflow = StateGraph(GenerateDocumentsV2State)
    workflow.add_node("ingest_llm", _make_ingestion_node(store))
    workflow.add_node("requirement_filter", _make_filter_node(store))
    
    workflow.add_edge(START, "ingest_llm")
    workflow.add_edge("ingest_llm", "requirement_filter")
    workflow.add_edge("requirement_filter", END)
    
    return workflow.compile()


def _make_ingestion_node(store: PipelineArtifactStore):
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        source = state["source"]
        job_id = state["job_id"]
        
        from src.core.ai.generate_documents_v2.nodes.ingestion import (
            run_ingestion, 
            build_ingestion_chain,
            load_ingestion_artifact_bundle
        )
        
        bundle = load_ingestion_artifact_bundle(
            source=source,
            job_id=job_id,
            jobs_root=store.root,
        )
        
        result = run_ingestion(
            source=source,
            job_id=job_id,
            job_bundle=bundle,
            chain=build_ingestion_chain(),
            store=store,
        )
        return result
    return node


def _make_filter_node(store: PipelineArtifactStore):
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        source = state["source"]
        job_id = state["job_id"]
        
        from src.core.ai.generate_documents_v2.contracts.job import JobKG
        from src.core.ai.generate_documents_v2.nodes.requirement_filter import (
            run_requirement_filter,
            build_requirement_filter_chain
        )
        
        job_kg = JobKG.model_validate(state["job_kg"])
        
        result = run_requirement_filter(
            source=source,
            job_id=job_id,
            job_kg=job_kg,
            chain=build_requirement_filter_chain(),
            store=store,
        )
        return result
    return node
