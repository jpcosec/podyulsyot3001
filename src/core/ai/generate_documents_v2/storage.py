"""Artifact persistence for the generate_documents_v2 pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.data_manager import DataManager


class PipelineArtifactStore:
    """Manage per-stage JSON artifacts for the generate_documents_v2 pipeline."""

    def __init__(self, root: str | Path = "data/jobs") -> None:
        self.root = Path(root)
        self._dm = DataManager(self.root)

    def _stage_dir(self, source: str, job_id: str, stage: str) -> Path:
        return self.root / source / job_id / "nodes" / "generate_documents_v2" / stage

    def write_stage(
        self,
        source: str,
        job_id: str,
        stage: str,
        payload: dict[str, Any],
    ) -> dict[str, str]:
        path = self._stage_dir(source, job_id, stage) / "current.json"
        self._dm.write_json_path(path, payload)
        return {f"{stage}_ref": str(path)}

    def load_stage(self, source: str, job_id: str, stage: str) -> dict[str, Any] | None:
        path = self._stage_dir(source, job_id, stage) / "current.json"
        if not path.exists():
            return None
        return self._dm.read_json_path(path)

    def sha256_file(self, path: str | Path) -> str:
        return self._dm.sha256_path(path)
