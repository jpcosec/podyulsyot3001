from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from src.interfaces.api.config import load_settings
from src.interfaces.api.models import to_dict
from src.interfaces.api.read_models import (
    _read_json_safe,
    build_job_timeline,
    build_view_one_payload,
    build_view_three_payload,
    build_view_two_payload,
    load_document,
    load_editor_state,
    load_match_review_payload,
    load_stage_outputs,
    save_document,
    save_editor_state,
)
from src.core.io.workspace_manager import WorkspaceManager

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/{source}/{job_id}/timeline")
def job_timeline(source: str, job_id: str) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    timeline = build_job_timeline(data_root, source, job_id)
    return to_dict(timeline)


@router.get("/{source}/{job_id}/review/match")
def match_review(source: str, job_id: str) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    payload = load_match_review_payload(data_root, source, job_id)
    return payload


@router.get("/{source}/{job_id}/view2")
def view_two_payload(source: str, job_id: str) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    payload = build_view_two_payload(data_root, source, job_id)
    return to_dict(payload)


@router.get("/{source}/{job_id}/view1")
def view_one_payload(source: str, job_id: str) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    payload = build_view_one_payload(data_root, source, job_id)
    return to_dict(payload)


@router.get("/{source}/{job_id}/view3")
def view_three_payload(source: str, job_id: str) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    payload = build_view_three_payload(data_root, source, job_id)
    return to_dict(payload)


@router.get("/{source}/{job_id}/editor/{node_name}/state")
def editor_state(source: str, job_id: str, node_name: str) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    try:
        return load_editor_state(data_root, source, job_id, node_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{source}/{job_id}/editor/{node_name}/state")
def update_editor_state(
    source: str,
    job_id: str,
    node_name: str,
    payload: dict[str, Any] = Body(...),
) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    try:
        return save_editor_state(data_root, source, job_id, node_name, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{source}/{job_id}/stage/{stage}/outputs")
def stage_outputs(source: str, job_id: str, stage: str) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    return load_stage_outputs(data_root, source, job_id, stage)


@router.get("/{source}/{job_id}/documents/{doc_key}")
def document_payload(source: str, job_id: str, doc_key: str) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    try:
        return load_document(data_root, source, job_id, doc_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{source}/{job_id}/documents/{doc_key}")
def update_document_payload(
    source: str,
    job_id: str,
    doc_key: str,
    payload: dict[str, Any] = Body(...),
) -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    content = payload.get("content")
    if not isinstance(content, str):
        raise HTTPException(status_code=400, detail="content must be a string")
    try:
        return save_document(data_root, source, job_id, doc_key, content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{source}/{job_id}/evidence-bank")
def get_evidence_bank(source: str, job_id: str) -> dict:
    """Return evidence entries from the candidate profile."""
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    workspace = WorkspaceManager(data_root)
    evidence_dir = workspace.job_root(source, job_id) / "profile" / "evidence"

    items = []
    if evidence_dir.exists():
        for f in sorted(evidence_dir.glob("*.json")):
            data = _read_json_safe(f)
            if data:
                items.append(
                    {
                        "id": f.stem,
                        "title": data.get("title", data.get("name", f.stem)),
                        "category": data.get("category", "unknown"),
                        "tags": data.get("tags", data.get("skills", [])),
                        "summary": data.get("summary", data.get("description", "")),
                        "source_path": str(
                            f.relative_to(workspace.job_root(source, job_id))
                        ),
                    }
                )

    return {"source": source, "job_id": job_id, "items": items}


@router.get("/{source}/{job_id}/package/files")
def get_package_files(source: str, job_id: str) -> dict:
    """List files in the package directory if it exists."""
    import os

    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    workspace = WorkspaceManager(data_root)
    package_dir = workspace.job_root(source, job_id) / "nodes" / "package"

    files = []
    if package_dir.exists():
        for f in sorted(package_dir.rglob("*")):
            if f.is_file():
                size_kb = os.path.getsize(f) / 1024
                files.append(
                    {
                        "name": f.name,
                        "path": str(f.relative_to(workspace.job_root(source, job_id))),
                        "size_kb": round(size_kb, 1),
                    }
                )

    return {"source": source, "job_id": job_id, "files": files}


@router.get("/{source}/{job_id}/profile/summary")
def get_profile_summary(source: str, job_id: str) -> dict:
    """Return candidate profile summary."""
    settings = load_settings()
    data_root = Path(settings.data_root)
    job_root = data_root / source / job_id
    if not job_root.exists():
        raise HTTPException(status_code=404, detail="job not found")

    workspace = WorkspaceManager(data_root)
    evidence_dir = workspace.job_root(source, job_id) / "profile" / "evidence"

    items_by_cat: dict[str, int] = {}
    if evidence_dir.exists():
        for f in evidence_dir.glob("*.json"):
            data = _read_json_safe(f)
            if data:
                cat = data.get("category", "unknown")
                items_by_cat[cat] = items_by_cat.get(cat, 0) + 1

    return {
        "source": source,
        "job_id": job_id,
        "skills_count": items_by_cat.get("skill", 0),
        "projects_count": items_by_cat.get("project", 0),
        "education_count": items_by_cat.get("education", 0),
        "experience_count": items_by_cat.get("experience", 0),
    }
