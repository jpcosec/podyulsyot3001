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
from src.nodes.package.contract import (
    PackageInputState,
    PackageManifest,
    PackagedArtifact,
)
from src.nodes.render.contract import RenderStateEnvelope


_EXPECTED_DOC_KEYS = ("cv", "motivation_letter", "application_email")


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    validated = PackageInputState.model_validate(dict(state))
    source = validated.source
    job_id = validated.job_id

    workspace = WorkspaceManager()
    reader = ArtifactReader(workspace)
    writer = ArtifactWriter(workspace)
    job_root = workspace.job_root(source, job_id)

    render_state_path = workspace.node_stage_artifact(
        source=source,
        job_id=job_id,
        node_name="render",
        stage="approved",
        filename="state.json",
    )
    render_envelope = RenderStateEnvelope.model_validate(
        reader.read_json(render_state_path)
    )
    _validate_render_envelope(render_envelope)

    artifacts: dict[str, PackagedArtifact] = _package_documents(
        source,
        job_id,
        workspace,
        reader,
        writer,
        render_envelope,
    )
    manifest = PackageManifest(
        source=source,
        job_id=job_id,
        packaged_at=datetime.now(timezone.utc).isoformat(),
        render_state_ref=_job_relative(render_state_path, source, job_id, workspace),
        artifacts=artifacts,
    )

    manifest_path = writer.write_text(
        workspace.resolve_under_job(source, job_id, "final/manifest.json"),
        manifest.model_dump_json(indent=2),
    )
    approved_path = writer.write_node_stage_json(
        source=source,
        job_id=job_id,
        node_name="package",
        stage="approved",
        filename="state.json",
        payload={
            "manifest_ref": _job_relative(manifest_path, source, job_id, workspace),
            "artifact_count": len(artifacts),
        },
    )

    artifact_refs = dict(state.get("artifact_refs") or {})
    artifact_refs["last_proposed_state_ref"] = _job_relative(
        approved_path, source, job_id, workspace
    )

    result = {
        **dict(state),
        "current_node": "package",
        "status": "completed",
        "artifact_refs": artifact_refs,
        "package_manifest_ref": _job_relative(manifest_path, source, job_id, workspace),
    }
    _write_execution_metadata("package", result)
    return result


def _package_documents(
    source: str,
    job_id: str,
    workspace: WorkspaceManager,
    reader: ArtifactReader,
    writer: ArtifactWriter,
    render_envelope: RenderStateEnvelope,
) -> dict[str, PackagedArtifact]:
    out: dict[str, PackagedArtifact] = {}
    for doc_key in _EXPECTED_DOC_KEYS:
        document = render_envelope.documents[doc_key]
        render_path = workspace.resolve_under_job(source, job_id, document.rendered_ref)
        content = reader.read_text(render_path)
        actual_hash = ProvenanceService.sha256_text(content)
        if actual_hash != document.sha256:
            raise ValueError(f"render approved hash mismatch for {doc_key}")

        filename = Path(document.rendered_ref).name
        final_path = writer.write_text(
            workspace.resolve_under_job(source, job_id, f"final/{filename}"),
            content,
        )
        out[doc_key] = PackagedArtifact(
            path=_job_relative(final_path, source, job_id, workspace),
            sha256=actual_hash,
        )
    return out


def _job_relative(
    path: Path, source: str, job_id: str, workspace: WorkspaceManager
) -> str:
    job_root = workspace.job_root(source, job_id).resolve()
    return str(path.resolve().relative_to(job_root))


def _validate_render_envelope(render_envelope: RenderStateEnvelope) -> None:
    if render_envelope.node != "render":
        raise ValueError("render approved state must have node='render'")
    if set(render_envelope.documents) != set(_EXPECTED_DOC_KEYS):
        raise ValueError("render approved state documents do not match expected keys")


def _write_execution_metadata(node_name: str, state: Mapping[str, Any]) -> None:
    workspace = WorkspaceManager()
    writer = ArtifactWriter(workspace)
    service = ObservabilityService(workspace, writer)
    service.write_node_execution_snapshot(node_name=node_name, state=state)
