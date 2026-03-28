"""Pandoc DOCX engine adapter."""

from __future__ import annotations

from src.render.documents.base import DocumentPayload
from src.render.engines.base import EngineAdapter, ResolvedRenderConfig
from src.render.engines.docx.renderer import DocxRenderer


class PandocDocxEngineAdapter(EngineAdapter):
    """Render Markdown payloads to DOCX using Pandoc."""

    engine_name = "docx"

    def __init__(self, renderer: DocxRenderer | None = None):
        self.renderer = renderer or DocxRenderer()

    def render(self, payload: DocumentPayload, config: ResolvedRenderConfig):
        if payload.source_kind != "markdown":
            raise ValueError("Pandoc DOCX adapter only supports Markdown payloads")
        return self.renderer.render_markdown(
            payload.source_path,
            config.output_path,
            reference_doc=config.reference_doc,
            lua_filters=config.lua_filters,
            asset_roots=config.asset_roots,
            metadata=config.metadata,
        )
