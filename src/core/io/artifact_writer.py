from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.core.io.workspace_manager import WorkspaceManager


class ArtifactWriter:
    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace

    def write_text(self, path: Path, content: str) -> Path:
        self.workspace.ensure_parent(path)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=str(path.parent),
        ) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_name = temp_file.name
        os.replace(temp_name, path)
        return path

    def write_json(self, path: Path, payload: Mapping[str, Any] | list[Any]) -> Path:
        encoded = json.dumps(payload, indent=2, ensure_ascii=False)
        return self.write_text(path, encoded)

    def write_node_stage_text(
        self,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
        content: str,
    ) -> Path:
        artifact = self.workspace.node_stage_artifact(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        return self.write_text(artifact, content)

    def write_node_stage_json(
        self,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
        payload: Mapping[str, Any] | list[Any],
    ) -> Path:
        artifact = self.workspace.node_stage_artifact(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        return self.write_json(artifact, payload)
