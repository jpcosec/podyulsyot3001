"""Motivation letter document adapter."""

from __future__ import annotations

from pathlib import Path

from src.core.tools.render.documents.base import DocumentAdapter, DocumentPayload
from src.core.tools.render.request import RenderRequest
from src.core.tools.render.shared.paths import JobRenderPaths


class LetterDocumentAdapter(DocumentAdapter):
    """Normalize motivation letter Markdown inputs."""

    document_type = "letter"
    default_style = "default"

    def resolve_job_source(self, request: RenderRequest, paths: JobRenderPaths) -> Path:
        candidates = [
            paths.generate_dir / f"cover_letter.{request.language}.md",
            paths.generate_dir / "cover_letter.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            f"cover_letter markdown not found in {paths.generate_dir}"
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
