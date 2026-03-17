from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.interfaces.api.config import load_settings
from src.interfaces.api.models import to_dict
from src.interfaces.api.read_models import (
    build_job_timeline,
    build_view_one_payload,
    build_view_three_payload,
    build_view_two_payload,
    load_match_review_payload,
)

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
