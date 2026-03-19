from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.interfaces.api.config import load_settings
from src.interfaces.api.routers.health import router as health_router
from src.interfaces.api.routers.jobs import router as jobs_router
from src.interfaces.api.routers.neo4j import router as neo4j_router
from src.interfaces.api.routers.portfolio import router as portfolio_router


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="PhD 2.0 Review API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.ui_origin],
        allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(portfolio_router)
    app.include_router(jobs_router)
    app.include_router(neo4j_router)
    return app


app = create_app()
