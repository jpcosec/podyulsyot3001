"""Pipeline render node adapters for schema-v0."""

from __future__ import annotations

import logging

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.shared.log_tags import LogTag
from src.tools.render import RenderCoordinator, RenderRequest

logger = logging.getLogger(__name__)


def make_render_node(data_manager: DataManager):
    """Create the schema-v0 render adapter."""

    async def render_node(state: GraphState) -> dict:
        source = state["source"]
        job_id = state["job_id"]
        artifact_refs = dict(state.get("artifact_refs", {}))

        try:
            coordinator = RenderCoordinator()
            rendered = []
            if cv_ref := artifact_refs.get("cv_markdown_ref"):
                del cv_ref
                rendered_cv = coordinator.render(
                    RenderRequest(
                        document_type="cv",
                        engine="tex",
                        language="en",
                        source=source,
                        source_kind="job",
                        job_id=job_id,
                    )
                )
                artifact_refs["rendered_cv_ref"] = str(rendered_cv)
                rendered.append("cv")

            if letter_ref := artifact_refs.get("letter_markdown_ref"):
                del letter_ref
                rendered_letter = coordinator.render(
                    RenderRequest(
                        document_type="letter",
                        engine="tex",
                        language="en",
                        source=source,
                        source_kind="job",
                        job_id=job_id,
                    )
                )
                artifact_refs["rendered_letter_ref"] = str(rendered_letter)
                rendered.append("letter")

            logger.info(
                f"{LogTag.OK} Published render-stage artifacts for {source}/{job_id}"
            )
            return {
                "artifact_refs": artifact_refs,
                "render_summary": {"generated": rendered},
                "current_node": "render",
                "status": "running",
            }
        except Exception as exc:
            logger.error(f"{LogTag.FAIL} Render node failed: {exc}")
            return {
                "current_node": "render",
                "status": "failed",
                "error_state": {"node": "render", "message": str(exc), "details": None},
            }

    return render_node
