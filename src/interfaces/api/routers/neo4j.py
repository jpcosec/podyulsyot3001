from __future__ import annotations

from fastapi import APIRouter

from src.interfaces.api.config import load_settings
from src.interfaces.api.neo4j_client import check_neo4j
from src.interfaces.api.neo4j_schema import apply_schema_constraints

router = APIRouter(prefix="/api/v1/neo4j", tags=["neo4j"])


@router.get("/health")
def neo4j_health() -> dict:
    settings = load_settings()
    health = check_neo4j(settings)
    return {"ok": health.ok, "message": health.message}


@router.post("/bootstrap-schema")
def neo4j_bootstrap_schema() -> dict:
    settings = load_settings()
    result = apply_schema_constraints(settings)
    return {"ok": result.ok, "applied": result.applied, "message": result.message}
