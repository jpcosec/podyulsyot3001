"""Pipeline match-skill node adapters for schema-v0."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

from src.ai.match_skill.storage import MatchArtifactStore
from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def _load_profile_evidence(state: GraphState, data_manager: DataManager) -> list[dict]:
    source = state["source"]
    job_id = state["job_id"]
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


# TODO(future): remove this wrapper — match_skill should be a native subgraph in the pipeline graph — see future_docs/issues/pipeline_graph_unification.md
def make_match_skill_node(data_manager: DataManager):
    """Create the match-skill adapter rooted in ``data/jobs``."""

    async def match_skill_node(state: GraphState) -> dict:
        from src.ai.match_skill.graph import build_match_skill_graph

        source = state["source"]
        job_id = state["job_id"]

        try:
            bridge_state = data_manager.read_json_artifact(
                source=source,
                job_id=job_id,
                node_name="extract_bridge",
                stage="proposed",
                filename="state.json",
            )
            requirements = bridge_state.get("requirements", [])
            profile_evidence = _load_profile_evidence(state, data_manager)
            store = MatchArtifactStore(data_manager.jobs_root)
            app = build_match_skill_graph(
                artifact_store=store,
                checkpointer=InMemorySaver(),
            )
            result = await app.ainvoke(
                {
                    "source": source,
                    "job_id": job_id,
                    "requirements": requirements,
                    "profile_evidence": profile_evidence,
                    "artifact_refs": state.get("artifact_refs", {}),
                },
                config={"configurable": {"thread_id": f"{source}_{job_id}"}},
            )
            refs = {**state.get("artifact_refs", {}), **result.get("artifact_refs", {})}
            logger.info(f"{LogTag.OK} Match skill completed for {source}/{job_id}")
            return {
                "artifact_refs": refs,
                "current_node": "match_skill",
                "status": result.get("status", "running"),
            }
        except Exception as exc:
            logger.error(f"{LogTag.FAIL} Match skill node failed: {exc}")
            return {
                "current_node": "match_skill",
                "status": "failed",
                "error_state": {
                    "node": "match_skill",
                    "message": str(exc),
                    "details": None,
                },
            }

    return match_skill_node
