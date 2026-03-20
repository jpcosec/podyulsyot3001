from __future__ import annotations

import re
from pathlib import Path

_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class WorkspaceManager:
    def __init__(self, jobs_root: str | Path = "data/jobs"):
        self.jobs_root = Path(jobs_root)

    def _validated_segment(self, value: str, field: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{field} is required")
        if not _SEGMENT_RE.match(cleaned):
            raise ValueError(f"{field} contains unsupported characters: {value!r}")
        return cleaned

    def _safe_relative_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise ValueError("relative_path must not be absolute")
        if any(part == ".." for part in candidate.parts):
            raise ValueError("relative_path must not contain '..'")
        return candidate

    def job_root(self, source: str, job_id: str) -> Path:
        src = self._validated_segment(source, "source")
        jid = self._validated_segment(job_id, "job_id")
        return self.jobs_root / src / jid

    def node_root(self, source: str, job_id: str, node_name: str) -> Path:
        node = self._validated_segment(node_name, "node_name")
        return self.job_root(source, job_id) / "nodes" / node

    def node_stage_dir(
        self,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
    ) -> Path:
        stage_name = self._validated_segment(stage, "stage")
        return self.node_root(source, job_id, node_name) / stage_name

    def node_stage_artifact(
        self,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
    ) -> Path:
        file_name = self._validated_segment(filename, "filename")
        return self.node_stage_dir(source, job_id, node_name, stage) / file_name

    def resolve_under_job(self, source: str, job_id: str, relative_path: str) -> Path:
        root = self.job_root(source, job_id).resolve()
        relative = self._safe_relative_path(relative_path)
        resolved = (root / relative).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("relative_path escapes job root")
        return resolved

    @staticmethod
    def ensure_parent(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
