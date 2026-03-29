"""Base classes for engine adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field

from src.core.tools.render.documents.base import DocumentPayload


class ResolvedRenderConfig(BaseModel):
    """Fully resolved configuration used by engine adapters."""

    document_type: str
    style: str
    language: str
    engine: str
    template_path: Path | None = None
    reference_doc: Path | None = None
    lua_filters: list[Path] = Field(default_factory=list)
    asset_roots: list[Path] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    output_path: Path
    build_dir: Path


class EngineAdapter(ABC):
    """Render a normalized payload using a specific backend."""

    engine_name: str

    @abstractmethod
    def render(self, payload: DocumentPayload, config: ResolvedRenderConfig) -> Path:
        """Render a normalized payload to the configured output path."""
