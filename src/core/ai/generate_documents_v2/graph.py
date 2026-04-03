"""Top-level orchestration for the generate_documents_v2 pipeline.

This graph assembles the modular stage subgraphs into a unified end-to-end
application document generation engine.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.core.ai.generate_documents_v2.state import GenerateDocumentsV2State
from src.core.ai.generate_documents_v2.storage import PipelineArtifactStore
from src.core.ai.generate_documents_v2.profile_loader import (
    load_profile_kg,
    load_section_mapping,
)
from src.core.ai.generate_documents_v2.subgraphs.stage1_ingestion import build_stage1_ingestion
from src.core.ai.generate_documents_v2.subgraphs.stage2_semantic_bridge import build_stage2_semantic_bridge
from src.core.ai.generate_documents_v2.subgraphs.stage3_macroplanning import build_stage3_macroplanning
from src.core.ai.generate_documents_v2.subgraphs.stage4_microplanning import build_stage4_microplanning
from src.core.ai.generate_documents_v2.subgraphs.stage5_assembly_render import build_stage5_assembly_render
from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_generate_documents_v2_graph(
    *, store: PipelineArtifactStore | None = None
) -> Any:
    """Build the end-to-end modular pipeline graph."""
    artifact_store = store or PipelineArtifactStore()
    workflow = StateGraph(GenerateDocumentsV2State)

    # 1. Register Nodes (Subgraphs & Helpers)
    workflow.add_node("load_profile_mapping", _make_load_inputs_node())
    workflow.add_node("stage_1_ingestion", build_stage1_ingestion(artifact_store))
    workflow.add_node("stage_2_semantic_bridge", build_stage2_semantic_bridge(artifact_store))
    workflow.add_node("stage_3_macroplanning", build_stage3_macroplanning(artifact_store))
    workflow.add_node("stage_4_microplanning", build_stage4_microplanning(artifact_store))
    workflow.add_node("stage_5_assembly_render", build_stage5_assembly_render(artifact_store))
    workflow.add_node("profile_updater", _make_profile_updater_node())

    # 2. Define Edges
    workflow.add_edge(START, "load_profile_mapping")
    workflow.add_edge("load_profile_mapping", "stage_1_ingestion")
    workflow.add_edge("stage_1_ingestion", "stage_2_semantic_bridge")
    
    workflow.add_conditional_edges(
        "stage_2_semantic_bridge",
        lambda s: s.get("match_outcome", "approved"),
        {"approved": "stage_3_macroplanning", "rejected": END},
    )
    workflow.add_conditional_edges(
        "stage_3_macroplanning",
        lambda s: s.get("blueprint_outcome", "approved"),
        {"approved": "stage_4_microplanning", "rejected": END},
    )
    workflow.add_edge("stage_4_microplanning", "stage_5_assembly_render")
    
    workflow.add_conditional_edges(
        "stage_5_assembly_render",
        _route_after_stage5,
        {
            "profile_updater": "profile_updater",
            "stage_4_microplanning": "stage_4_microplanning",
            "__end__": END,
        },
    )
    workflow.add_edge("profile_updater", END)

    return workflow.compile()


def create_studio_graph() -> Any:
    """Entry point for LangGraph Studio."""
    return build_generate_documents_v2_graph()


# ---------------------------------------------------------------------------
# Routing & Helpers
# ---------------------------------------------------------------------------

def _route_after_stage5(state: GenerateDocumentsV2State) -> str:
    outcome = state.get("bundle_outcome", "approved")
    if outcome == "rejected":
        return "__end__"
    if outcome == "content_regen":
        return "stage_4_microplanning"
    if state.get("auto_approve_review", True):
        return "profile_updater"
    return "__end__"


def _make_load_inputs_node():
    """Stage 0 helper: loading shared profile and mapping resources."""
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        source = state["source"]
        job_id = state["job_id"]
        
        # 1. Profile Data
        if state.get("profile_evidence"):
            logger.info("%s Using injected profile evidence for %s/%s", LogTag.FAST, source, job_id)
            raw_profile = state["profile_evidence"]
            from src.core.ai.generate_documents_v2.profile_loader import build_profile_kg
            profile_kg = build_profile_kg(raw_profile)
        else:
            profile_path = state.get("profile_path") or os.getenv("PROFILE_BASE_DATA_PATH")
            if not profile_path:
                profile_path = "data/reference_data/profile/base_profile/profile_base_data.json"
            
            logger.info("%s Loading profile from %s for %s/%s", LogTag.FAST, profile_path, source, job_id)
            profile_kg = load_profile_kg(profile_path)
            raw_profile = DataManager().read_json_path(profile_path)
            
        # 2. Section Mapping
        mapping_path = state.get("mapping_path") or "data/reference_data/profile/section_mapping.json"
        section_mapping = load_section_mapping(mapping_path)
        
        return {
            "profile_kg": profile_kg.model_dump(),
            "profile_data": raw_profile,
            "section_mapping": [m.model_dump() for m in section_mapping],
            "status": "inputs_loaded",
        }
    return node


def _make_profile_updater_node():
    """Stage 6 helper: applying successful application insights back to profile."""
    def node(state: GenerateDocumentsV2State) -> dict[str, Any]:
        logger.info("%s Profile updater: (no-op in v2 prototype)", LogTag.OK)
        return {"status": "completed"}
    return node


__all__ = [
    "GenerateDocumentsV2State",
    "build_generate_documents_v2_graph",
    "create_studio_graph",
]
