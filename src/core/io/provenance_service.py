from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.core.io.artifact_writer import ArtifactWriter
from src.core.io.workspace_manager import WorkspaceManager


class ProvenanceService:
    @staticmethod
    def sha256_bytes(payload: bytes) -> str:
        return f"sha256:{hashlib.sha256(payload).hexdigest()}"

    @staticmethod
    def sha256_text(payload: str) -> str:
        return ProvenanceService.sha256_bytes(payload.encode("utf-8"))

    @staticmethod
    def sha256_json(payload: Mapping[str, Any] | list[Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return ProvenanceService.sha256_text(canonical)

    @staticmethod
    def sha256_file(path: Path) -> str:
        return ProvenanceService.sha256_bytes(path.read_bytes())


class ObservabilityService:
    def __init__(self, workspace: WorkspaceManager, writer: ArtifactWriter):
        self.workspace = workspace
        self.writer = writer

    def write_node_execution_snapshot(
        self,
        *,
        node_name: str,
        state: Mapping[str, Any],
    ) -> Path | None:
        source, job_id = _job_scope(state)
        if source is None or job_id is None:
            return None

        payload = {
            "schema_version": "1.0",
            "node": node_name,
            "source": source,
            "job_id": job_id,
            "run_id": str(state.get("run_id", "")),
            "current_node": str(state.get("current_node", "")),
            "status": str(state.get("status", "")),
            "review_decision": state.get("review_decision"),
            "pending_gate": state.get("pending_gate"),
            "artifact_refs": dict(state.get("artifact_refs") or {}),
            "error_state": _mapping_or_none(state.get("error_state")),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.writer.write_node_stage_json(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage="meta",
            filename="execution.json",
            payload=payload,
        )

    def write_run_summary(self, state: Mapping[str, Any]) -> Path | None:
        source, job_id = _job_scope(state)
        if source is None or job_id is None:
            return None

        payload = {
            "schema_version": "1.0",
            "source": source,
            "job_id": job_id,
            "run_id": str(state.get("run_id", "")),
            "current_node": str(state.get("current_node", "")),
            "status": str(state.get("status", "")),
            "review_decision": state.get("review_decision"),
            "pending_gate": state.get("pending_gate"),
            "artifact_refs": dict(state.get("artifact_refs") or {}),
            "error_state": _mapping_or_none(state.get("error_state")),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        summary_path = self.workspace.resolve_under_job(
            source, job_id, "graph/run_summary.json"
        )
        return self.writer.write_json(summary_path, payload)


def _job_scope(state: Mapping[str, Any]) -> tuple[str | None, str | None]:
    source = state.get("source")
    job_id = state.get("job_id")
    if not isinstance(source, str) or not source.strip():
        return None, None
    if not isinstance(job_id, str) or not job_id.strip():
        return None, None
    return source.strip(), job_id.strip()


def _mapping_or_none(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None
