"""Pipeline translate node — verify-only adapter.

Translation is performed as a CLI pre-processing step (src.core.tools.translator.main).
This node verifies the translated artifact is present and populates artifact_refs.
"""

from __future__ import annotations

import logging

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def make_translate_node(data_manager: DataManager):
    """Create the translate verify node."""

    def translate_node(state: GraphState) -> dict:
        source = state["source"]
        job_id = state["job_id"]
        refs = dict(state.get("artifact_refs", {}))

        state_path = data_manager.artifact_path(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="state.json",
        )

        if not state_path.exists():
            logger.error(
                "%s translate/proposed/state.json missing for %s/%s — run 'translate' step before pipeline",
                LogTag.FAIL,
                source,
                job_id,
            )
            return {
                "current_node": "translate",
                "status": "failed",
                "error_state": {
                    "node": "translate",
                    "message": (
                        f"translate/proposed/state.json not found for {source}/{job_id}. "
                        "Translation must be run before launching the pipeline."
                    ),
                    "details": None,
                },
            }

        refs["translated_state"] = str(state_path)

        content_path = data_manager.artifact_path(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="content.md",
        )
        if content_path.exists():
            refs["translated_content"] = str(content_path)

        logger.info("%s Translate artifact verified for %s/%s", LogTag.OK, source, job_id)
        return {
            "artifact_refs": refs,
            "current_node": "translate",
            "status": "running",
        }

    return translate_node
