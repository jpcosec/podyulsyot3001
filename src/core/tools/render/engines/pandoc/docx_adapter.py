"""Pandoc DOCX engine adapter."""

from __future__ import annotations

from pathlib import Path

from src.core.tools.render.documents.base import DocumentPayload
from src.core.tools.render.engines.base import EngineAdapter, ResolvedRenderConfig
from src.core.tools.render.engines.pandoc.renderer import PandocRenderer


class PandocDocxEngineAdapter(EngineAdapter):
    """Render Markdown payloads to DOCX using Pandoc."""

    engine_name = "docx"

    def __init__(self, renderer: PandocRenderer | None = None):
        self.renderer = renderer or PandocRenderer()

    def render(self, payload: DocumentPayload, config: ResolvedRenderConfig) -> Path:
        """Render a markdown payload to DOCX.

        Args:
            payload: Normalized document payload to render.
            config: Resolved engine/template/output configuration.

        Returns:
            The rendered output path.
        """
        if payload.source_kind != "markdown":
            raise ValueError("Pandoc DOCX adapter only supports Markdown payloads")
        return self.renderer.render(
            payload.source_path,
            config.output_path,
            target_format="docx",
            template_path=config.reference_doc,
            lua_filters=config.lua_filters,
            asset_roots=config.asset_roots,
            metadata=config.metadata,
        )
