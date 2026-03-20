from __future__ import annotations

from typing import Any

from src.core.io.artifact_writer import ArtifactWriter
from src.core.io.workspace_manager import WorkspaceManager


class ScrapingArtifactStore:
    def __init__(self, workspace: WorkspaceManager | None = None) -> None:
        self.workspace = workspace or WorkspaceManager()
        self.writer = ArtifactWriter(self.workspace)

    def write_json(
        self,
        source: str,
        job_id: str,
        stage: str,
        filename: str,
        payload: dict[str, Any] | list[Any],
    ) -> str:
        path = self.writer.write_node_stage_json(
            source=source,
            job_id=job_id,
            node_name="scrape",
            stage=stage,
            filename=filename,
            payload=payload,
        )
        return str(path)

    def write_raw_source_markdown(self, source: str, job_id: str, content: str) -> str:
        path = self.workspace.resolve_under_job(source, job_id, "raw/source_text.md")
        written = self.writer.write_text(path, content)
        return str(written)
