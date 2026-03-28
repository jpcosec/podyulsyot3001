"""Motivation letter document adapter."""

from __future__ import annotations

from pathlib import Path

from src.render.documents.base import DocumentAdapter, DocumentPayload
from src.render.request import RenderRequest
from src.render.shared.paths import JobRenderPaths


class LetterDocumentAdapter(DocumentAdapter):
    """Normalize motivation letter Markdown inputs."""

    document_type = "letter"
    default_style = "default"

    def resolve_job_source(self, request: RenderRequest, paths: JobRenderPaths) -> Path:
        candidates = [
            paths.application_dir / f"motivation_letter.{request.language}.md",
            paths.application_dir / "motivation_letter.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            f"motivation_letter markdown not found in {paths.application_dir}"
        )

    def build_payload(
        self, source_path: Path, request: RenderRequest
    ) -> DocumentPayload:
        del request
        return DocumentPayload(
            document_type=self.document_type,
            source_kind="markdown",
            source_path=source_path,
        )
