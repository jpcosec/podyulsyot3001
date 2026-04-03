"""Base classes for render document adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field

from src.core.tools.render.request import RenderRequest
from src.core.tools.render.shared.paths import JobRenderPaths


class DocumentPayload(BaseModel):
    """Normalized document payload returned by adapters."""

    document_type: str
    source_kind: str = Field(default="markdown")
    source_path: Path
    pandoc_metadata: dict[str, str] = Field(default_factory=dict)


class DocumentAdapter(ABC):
    """Document-specific normalization contract."""

    document_type: str
    default_style: str

    @abstractmethod
    def resolve_job_source(self, request: RenderRequest, paths: JobRenderPaths) -> Path:
        """Resolve the effective source path for job-based rendering."""

    @abstractmethod
    def build_payload(
        self, source_path: Path, request: RenderRequest
    ) -> DocumentPayload:
        """Normalize a source path into a payload for the engines."""

    def default_output_name(self, request: RenderRequest) -> str:
        """Return the default output name for direct rendering."""
        extension = ".docx" if request.engine == "docx" else ".pdf"
        return f"{self.document_type}{extension}"
