from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from src.interfaces.api.config import load_settings
from src.interfaces.api.models import to_dict
from src.interfaces.api.read_models import (
    build_base_cv_graph_payload,
    build_cv_profile_graph_payload,
    list_jobs,
    save_cv_profile_graph_payload,
    _deserialize_cv_profile_graph,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get("/summary")
def portfolio_summary() -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    jobs = list_jobs(data_root)

    totals = {
        "jobs": len(jobs),
        "completed": sum(1 for item in jobs if item.status == "completed"),
        "pending_review": sum(1 for item in jobs if item.status == "pending_review"),
        "running": sum(1 for item in jobs if item.status == "running"),
        "failed": sum(1 for item in jobs if item.status == "failed"),
    }

    return {
        "totals": totals,
        "jobs": [to_dict(item) for item in jobs],
    }


@router.get("/base-cv-graph")
def base_cv_graph() -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    payload = build_base_cv_graph_payload(data_root)
    return to_dict(payload)


@router.get("/cv-profile-graph")
def cv_profile_graph() -> dict:
    settings = load_settings()
    data_root = Path(settings.data_root)
    payload = build_cv_profile_graph_payload(data_root)
    return to_dict(payload)


@router.put("/cv-profile-graph")
def save_cv_profile_graph(body: dict[str, Any] = Body(...)) -> dict:
    try:
        payload = _deserialize_cv_profile_graph(body)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {exc}") from exc
    settings = load_settings()
    data_root = Path(settings.data_root)
    save_cv_profile_graph_payload(data_root, payload)
    logger.info("Saved CV profile graph for %s", payload.profile_id)
    return to_dict(payload)
