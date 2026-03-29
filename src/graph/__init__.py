"""Top-level schema-v0 pipeline graph assembly."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.graph.nodes.extract_bridge import extract_requirements_from_job_posting
from src.graph.nodes.generate_documents import make_generate_documents_node
from src.graph.nodes.package import make_package_node
from src.graph.nodes.render import make_render_node
from src.graph.nodes.scrape import make_scrape_node
from src.graph.nodes.translate import make_translate_node


def _load_profile_evidence(
    state: GraphState, data_manager: DataManager, source: str, job_id: str
) -> list[dict]:
    """Load profile evidence from state ref, env path, or default location."""
    ref = state.get("profile_evidence_ref")
    if ref:
        return json.loads(Path(ref).read_text(encoding="utf-8"))
    path = os.getenv(
        "PROFILE_EVIDENCE_PATH",
        "data/reference_data/profile/base_profile/profile_base_data.json",
    )
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    evidence = payload.get("evidence", payload)
    ref_path = data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="pipeline_inputs",
        stage="proposed",
        filename="profile_evidence.json",
        data=evidence,
    )
    state["profile_evidence_ref"] = str(ref_path)
    return evidence


async def _extract_bridge_node(state: GraphState, data_manager: DataManager) -> dict:
    source = state["source"]
    job_id = state["job_id"]
    translated_state = data_manager.read_json_artifact(
        source=source,
        job_id=job_id,
        node_name="translate",
        stage="proposed",
        filename="state.json",
    )
    requirements = extract_requirements_from_job_posting(translated_state)
    requirements_dicts = [item.model_dump() for item in requirements]
    state_payload = {
        "source": source,
        "job_id": job_id,
        "requirements": requirements_dicts,
        "job_posting": translated_state,
    }
    refs = dict(state.get("artifact_refs", {}))
    bridge_state = data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="extract_bridge",
        stage="proposed",
        filename="state.json",
        data=state_payload,
    )
    refs["bridge_state"] = str(bridge_state)
    try:
        content = data_manager.read_text_artifact(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="content.md",
        )
        content_ref = data_manager.write_text_artifact(
            source=source,
            job_id=job_id,
            node_name="extract_bridge",
            stage="proposed",
            filename="content.md",
            content=content,
        )
        refs["bridge_content"] = str(content_ref)
    except FileNotFoundError:
        pass
    profile_evidence = _load_profile_evidence(state, data_manager, source, job_id)
    return {
        "artifact_refs": refs,
        "requirements": requirements_dicts,
        "profile_evidence": profile_evidence,
        "current_node": "extract_bridge",
        "status": "running",
    }


def make_extract_bridge_node(data_manager: DataManager):
    """Create the extract-bridge node adapter for schema-v0."""

    async def extract_bridge_node(state: GraphState) -> dict:
        return await _extract_bridge_node(state, data_manager)

    return extract_bridge_node


def _route_after_match_skill(state: GraphState) -> str:
    if state.get("status") in ("failed", "rejected"):
        return END
    return "generate_documents"


def _route_after_generate(state: GraphState) -> str:
    if state.get("status") == "failed":
        return END
    return "render"


def _route_after_render(state: GraphState) -> str:
    if state.get("status") == "failed":
        return END
    return "package"


def build_pipeline_graph(*, data_manager: DataManager | None = None) -> Any:
    """Build the schema-v0 top-level pipeline graph."""

    from src.ai.match_skill.graph import build_match_skill_graph
    from src.ai.match_skill.storage import MatchArtifactStore

    manager = data_manager or DataManager()
    match_skill_subgraph = build_match_skill_graph(
        artifact_store=MatchArtifactStore(manager.jobs_root),
        checkpointer=InMemorySaver(),
        interrupt_before=("human_review_node",),
        include_document_generation=False,
    )

    workflow = StateGraph(GraphState)
    workflow.add_node("scrape", make_scrape_node(manager))
    workflow.add_node("translate", make_translate_node(manager))
    workflow.add_node("extract_bridge", make_extract_bridge_node(manager))
    workflow.add_node("match_skill", match_skill_subgraph)
    workflow.add_node("generate_documents", make_generate_documents_node(manager))
    workflow.add_node("render", make_render_node(manager))
    workflow.add_node("package", make_package_node(manager))

    workflow.add_edge(START, "scrape")
    workflow.add_edge("scrape", "translate")
    workflow.add_edge("translate", "extract_bridge")
    workflow.add_edge("extract_bridge", "match_skill")
    workflow.add_conditional_edges("match_skill", _route_after_match_skill)
    workflow.add_conditional_edges("generate_documents", _route_after_generate)
    workflow.add_conditional_edges("render", _route_after_render)
    workflow.add_edge("package", END)

    return workflow.compile(checkpointer=InMemorySaver())


def create_studio_graph() -> Any:
    """Create a Studio-friendly compiled graph."""

    return build_pipeline_graph()


__all__ = ["GraphState", "build_pipeline_graph", "create_studio_graph"]
