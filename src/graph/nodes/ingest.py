"""Pipeline ingest node adapters for schema-v0."""

from __future__ import annotations

import logging

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.scraper.main import build_providers
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def _artifact_refs(
    data_manager: DataManager, source: str, job_id: str
) -> dict[str, str]:
    refs = {
        "ingest_state": str(
            data_manager.artifact_path(
                source=source,
                job_id=job_id,
                node_name="ingest",
                stage="proposed",
                filename="state.json",
            )
        )
    }
    if data_manager.artifact_exists(
        source=source,
        job_id=job_id,
        node_name="ingest",
        stage="proposed",
        filename="content.md",
    ):
        refs["ingest_content"] = str(
            data_manager.artifact_path(
                source=source,
                job_id=job_id,
                node_name="ingest",
                stage="proposed",
                filename="content.md",
            )
        )
    return refs


def make_ingest_node(data_manager: DataManager):
    """Create the ingest node adapter for canonical raw job artifacts."""

    async def ingest_node(state: GraphState) -> dict:
        source = state["source"]
        job_id = state.get("job_id")
        source_url = state.get("source_url")

        try:
            if job_id and data_manager.has_ingested_job(source, job_id):
                logger.info(
                    "%s Reusing canonical ingested artifact for %s/%s",
                    LogTag.CACHE,
                    source,
                    job_id,
                )
                return {
                    "artifact_refs": {
                        **state.get("artifact_refs", {}),
                        **_artifact_refs(data_manager, source, job_id),
                    },
                    "current_node": "ingest",
                    "status": "running",
                }

            if not source_url:
                raise FileNotFoundError(
                    f"No canonical ingest artifact for {source}/{job_id} and no source_url provided"
                )

            providers = build_providers(data_manager)
            adapter = providers[source]
            fetched_job_id = await adapter.fetch_job(source_url)
            if job_id and fetched_job_id != job_id:
                raise ValueError(
                    f"source_url resolved to job_id {fetched_job_id}, expected {job_id}"
                )
            resolved_job_id = job_id or fetched_job_id
            logger.info(
                "%s Ingested canonical raw artifact for %s/%s",
                LogTag.OK,
                source,
                resolved_job_id,
            )
            return {
                "job_id": resolved_job_id,
                "artifact_refs": {
                    **state.get("artifact_refs", {}),
                    **_artifact_refs(data_manager, source, resolved_job_id),
                },
                "current_node": "ingest",
                "status": "running",
            }
        except Exception as exc:
            logger.error("%s Ingest node failed: %s", LogTag.FAIL, exc)
            return {
                "current_node": "ingest",
                "status": "failed",
                "error_state": {"node": "ingest", "message": str(exc), "details": None},
            }

    return ingest_node
