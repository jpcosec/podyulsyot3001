"""CV document adapter."""

from __future__ import annotations

from pathlib import Path
from src.core.tools.render.documents.base import DocumentAdapter, DocumentPayload
from src.core.tools.render.request import RenderRequest
from src.core.tools.render.shared.paths import JobRenderPaths


class CVDocumentAdapter(DocumentAdapter):
    """Normalize CV markdown inputs for the render coordinator."""

    document_type = "cv"
    default_style = "classic"

    def resolve_job_source(self, request: RenderRequest, paths: JobRenderPaths) -> Path:
        """Resolve the best available CV source path for a render request.

        Args:
            request: Render request describing language and engine.
            paths: Precomputed render paths for the target job.

        Returns:
            The markdown CV path if present, otherwise the fallback profile path.
        """
        candidates = [
            paths.generate_dir / f"cv.{request.language}.md",
            paths.generate_dir / "cv.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"cv markdown not found in {paths.generate_dir}")

    def build_payload(
        self, source_path: Path, request: RenderRequest
    ) -> DocumentPayload:
        """Build the render payload for a CV source.

        Args:
            source_path: Resolved source path for the CV.
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
