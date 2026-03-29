"""Pipeline package node adapters for schema-v0."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def make_package_node(data_manager: DataManager):
    """Create the final packaging node for schema-v0 artifacts."""

    async def package_node(state: GraphState) -> dict:
        source = state["source"]
        job_id = state["job_id"]
        artifact_refs = dict(state.get("artifact_refs", {}))

        try:
            manifest: dict[str, object] = {
                "source": source,
                "job_id": job_id,
                "run_id": state.get("run_id"),
                "artifacts": {},
            }
            for name in (
                "rendered_cv_ref",
                "rendered_letter_ref",
                "email_markdown_ref",
            ):
                ref = artifact_refs.get(name)
                if not ref:
                    continue
                source_path = Path(ref)
                package_path = data_manager.write_bytes_artifact(
                    source=source,
                    job_id=job_id,
                    node_name="package",
                    stage="final",
                    filename=source_path.name,
                    content=source_path.read_bytes(),
                )
                manifest["artifacts"][name] = str(package_path)

            manifest_path = data_manager.write_json_artifact(
                source=source,
                job_id=job_id,
                node_name="package",
                stage="final",
                filename="manifest.json",
                data=json.loads(json.dumps(manifest)),
            )
            artifact_refs["package_manifest"] = str(manifest_path)

            logger.info(f"{LogTag.OK} Packaged final artifacts for {source}/{job_id}")
            return {
                "artifact_refs": artifact_refs,
                "current_node": "package",
                "status": "completed",
            }
        except Exception as exc:
            logger.error(f"{LogTag.FAIL} Package node failed: {exc}")
            return {
                "current_node": "package",
                "status": "failed",
                "error_state": {
                    "node": "package",
                    "message": str(exc),
                    "details": None,
                },
            }

    return package_node
