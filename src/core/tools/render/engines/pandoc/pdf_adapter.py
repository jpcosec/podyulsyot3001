"""Pandoc PDF engine adapter."""

from __future__ import annotations

from pathlib import Path

from src.core.tools.render.documents.base import DocumentPayload
from src.core.tools.render.engines.base import EngineAdapter, ResolvedRenderConfig
from src.core.tools.render.engines.pandoc.renderer import PandocRenderer


class PandocPdfEngineAdapter(EngineAdapter):
    """Render Markdown payloads to PDF using Pandoc."""

    engine_name = "tex"

    def __init__(self, renderer: PandocRenderer | None = None):
        self.renderer = renderer or PandocRenderer()

    def render(self, payload: DocumentPayload, config: ResolvedRenderConfig) -> Path:
        if payload.source_kind != "markdown":
            raise ValueError("Pandoc PDF adapter only supports Markdown payloads")
        return self.renderer.render(
            payload.source_path,
            config.output_path,
            target_format="pdf",
            template_path=config.template_path,
            lua_filters=config.lua_filters,
            asset_roots=config.asset_roots,
            metadata=config.metadata,
        )
