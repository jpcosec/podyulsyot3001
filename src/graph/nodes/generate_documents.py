"""Pipeline document-generation node adapters for schema-v0."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from src.ai.generate_documents.graph import (
    build_default_generate_documents_chain,
    generate_documents_bundle,
)
from src.ai.match_skill.storage import MatchArtifactStore
from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def _load_profile_base_data(data_manager: DataManager, state: GraphState) -> dict:
    source = state["source"]
    job_id = state["job_id"]
    profile_ref = state.get("artifact_refs", {}).get("profile_base_data")
    if profile_ref:
        return json.loads(Path(profile_ref).read_text(encoding="utf-8"))

    path = os.getenv(
        "PROFILE_DATA_PATH",
        "data/reference_data/profile/base_profile/profile_base_data.json",
    )
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    ref = data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="pipeline_inputs",
        stage="proposed",
        filename="profile_base_data.json",
        data=payload,
    )
    state.setdefault("artifact_refs", {})["profile_base_data"] = str(ref)
    return payload


def make_generate_documents_node(data_manager: DataManager):
    """Create the generate-documents adapter that persists outputs via DataManager."""

    async def generate_documents_node(state: GraphState) -> dict:
        source = state["source"]
        job_id = state["job_id"]

        try:
            chain = build_default_generate_documents_chain()
            bridge_state = data_manager.read_json_artifact(
                source=source,
                job_id=job_id,
                node_name="extract_bridge",
                stage="proposed",
                filename="state.json",
            )
            requirements = bridge_state.get("requirements", [])
            match_store = MatchArtifactStore(data_manager.jobs_root)
            approved_path = (
                match_store.job_root(source, job_id) / "approved" / "state.json"
            )
            approved_matches = match_store.load_json(approved_path).get("matches", [])
            source_hash = match_store.sha256_file(approved_path)
            profile_base = _load_profile_base_data(data_manager, state)

            deltas, rendered, review_assist = generate_documents_bundle(
                source=source,
                job_id=job_id,
                chain=chain,
                profile_base=profile_base,
                approved_matches_raw=approved_matches,
                requirements_raw=requirements,
                review_items=[],
                approved_state_hash=source_hash,
                state=state,
            )

            refs = {**state.get("artifact_refs", {})}
            refs["document_deltas_ref"] = str(
                data_manager.write_json_artifact(
                    source=source,
                    job_id=job_id,
                    node_name="generate_documents",
                    stage="proposed",
                    filename="deltas.json",
                    data=deltas.model_dump(),
                )
            )
            refs["cv_markdown_ref"] = str(
                data_manager.write_text_artifact(
                    source=source,
                    job_id=job_id,
                    node_name="generate_documents",
                    stage="proposed",
                    filename="cv.md",
                    content=rendered.cv_markdown,
                )
            )
            refs["letter_markdown_ref"] = str(
                data_manager.write_text_artifact(
                    source=source,
                    job_id=job_id,
                    node_name="generate_documents",
                    stage="proposed",
                    filename="cover_letter.md",
                    content=rendered.letter_markdown,
                )
            )
            refs["email_markdown_ref"] = str(
                data_manager.write_text_artifact(
                    source=source,
                    job_id=job_id,
                    node_name="generate_documents",
                    stage="proposed",
                    filename="email_body.txt",
                    content=rendered.email_markdown,
                )
            )
            refs["review_assist_ref"] = str(
                data_manager.write_json_artifact(
                    source=source,
                    job_id=job_id,
                    node_name="generate_documents",
                    stage="review",
                    filename="assist.json",
                    data=review_assist.model_dump(),
                )
            )
            logger.info(
                f"{LogTag.OK} Generated canonical documents for {source}/{job_id}"
            )
            return {
                "artifact_refs": refs,
                "generated_documents_summary": {"generated": ["cv", "letter", "email"]},
                "current_node": "generate_documents",
                "status": "running",
            }
        except Exception as exc:
            logger.error(f"{LogTag.FAIL} Generate documents node failed: {exc}")
            return {
                "current_node": "generate_documents",
                "status": "failed",
                "error_state": {
                    "node": "generate_documents",
                    "message": str(exc),
                    "details": None,
                },
            }

    return generate_documents_node
