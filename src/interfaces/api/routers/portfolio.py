from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from src.interfaces.api.config import load_settings
from src.interfaces.api.models import to_dict
from src.interfaces.api.read_models import list_jobs

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
