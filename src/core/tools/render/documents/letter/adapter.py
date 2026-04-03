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
        """Resolve the best available cover-letter markdown source.

        Args:
            request: Render request describing language and engine.
            paths: Precomputed render paths for the target job.

        Returns:
            The first matching markdown source path.
        """
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
        """Build the render payload for a letter source.

        Args:
            source_path: Resolved source path for the letter.
            request: Render request describing engine and language.

        Returns:
            The normalized document payload consumed by the render coordinator.
        """
        del request
        return DocumentPayload(
            document_type=self.document_type,
            source_kind="markdown",
            source_path=source_path,
        )
