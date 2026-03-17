from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiSettings:
    host: str
    port: int
    data_root: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    ui_origin: str


def load_settings() -> ApiSettings:
    return ApiSettings(
        host=os.getenv("PHD2_UI_API_HOST", "127.0.0.1"),
        port=int(os.getenv("PHD2_UI_API_PORT", "8010")),
        data_root=os.getenv("PHD2_DATA_ROOT", "data/jobs"),
        neo4j_uri=os.getenv("PHD2_NEO4J_URI", "bolt://127.0.0.1:7687"),
        neo4j_user=os.getenv("PHD2_NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("PHD2_NEO4J_PASSWORD", "phd2devpassword"),
        ui_origin=os.getenv("PHD2_UI_ORIGIN", "http://127.0.0.1:5173"),
    )
