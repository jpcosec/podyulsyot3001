from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.core.io import (
    ArtifactReader,
    ArtifactWriter,
    ObservabilityService,
    ProvenanceService,
    WorkspaceManager,
)
from src.nodes.render.contract import (
    RenderInputState,
    RenderStateEnvelope,
    RenderedDocumentRef,
)


_DOC_FILENAMES: dict[str, str] = {
    "cv": "cv.md",
    "motivation_letter": "motivation_letter.md",
    "application_email": "application_email.md",
}


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    validated = RenderInputState.model_validate(dict(state))
    source = validated.source
    job_id = validated.job_id

    workspace = WorkspaceManager()
    reader = ArtifactReader(workspace)
    writer = ArtifactWriter(workspace)
    job_root = workspace.job_root(source, job_id)

    documents: dict[str, RenderedDocumentRef] = _copy_render_inputs(
        source, job_id, workspace, reader, writer
    )
    envelope = RenderStateEnvelope(
        source=source,
        job_id=job_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        documents=documents,
    )
    approved_path = writer.write_node_stage_json(
        source=source,
        job_id=job_id,
        node_name="render",
        stage="approved",
        filename="state.json",
        payload=envelope.model_dump(mode="json"),
    )

    artifact_refs = dict(state.get("artifact_refs") or {})
    artifact_refs["last_proposed_state_ref"] = str(approved_path.relative_to(job_root))

    result = {
        **dict(state),
        "current_node": "render",
        "status": "running",
        "artifact_refs": artifact_refs,
        "rendered_documents": envelope.model_dump(mode="json")["documents"],
    }
    _write_execution_metadata("render", result)
    return result


def _copy_render_inputs(
    source: str,
    job_id: str,
    workspace: WorkspaceManager,
    reader: ArtifactReader,
    writer: ArtifactWriter,
) -> dict[str, RenderedDocumentRef]:
    out: dict[str, RenderedDocumentRef] = {}
    for doc_key, filename in _DOC_FILENAMES.items():
        source_path = workspace.node_stage_artifact(
            source=source,
            job_id=job_id,
            node_name="generate_documents",
            stage="proposed",
            filename=filename,
        )
        content = reader.read_text(source_path)
        rendered_path = writer.write_node_stage_text(
            source=source,
            job_id=job_id,
            node_name="render",
            stage="proposed",
            filename=filename,
            content=content,
        )
        out[doc_key] = RenderedDocumentRef(
            source_ref=_job_relative(source_path, source, job_id, workspace),
            rendered_ref=_job_relative(rendered_path, source, job_id, workspace),
            sha256=ProvenanceService.sha256_text(content),
        )
    return out


def _job_relative(
    path: Path, source: str, job_id: str, workspace: WorkspaceManager
) -> str:
    job_root = workspace.job_root(source, job_id)
    return str(path.relative_to(job_root))


def _write_execution_metadata(node_name: str, state: Mapping[str, Any]) -> None:
    workspace = WorkspaceManager()
    writer = ArtifactWriter(workspace)
    service = ObservabilityService(workspace, writer)
    service.write_node_execution_snapshot(node_name=node_name, state=state)
