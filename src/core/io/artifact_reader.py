from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.io.workspace_manager import WorkspaceManager


class ArtifactReader:
    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace

    def exists(self, path: Path) -> bool:
        return path.exists()

    def read_text(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_text(encoding="utf-8")

    def read_json(self, path: Path) -> Any:
        payload = self.read_text(path)
        return json.loads(payload)

    def read_node_stage_text(
        self,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
    ) -> str:
        artifact = self.workspace.node_stage_artifact(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        return self.read_text(artifact)

    def read_node_stage_json(
        self,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
    ) -> Any:
        artifact = self.workspace.node_stage_artifact(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        return self.read_json(artifact)
