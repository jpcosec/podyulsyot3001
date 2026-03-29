"""Registry for document adapters, engines, and style manifests."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from src.tools.render.documents.cv.adapter import CVDocumentAdapter
from src.tools.render.documents.letter.adapter import LetterDocumentAdapter
from src.tools.render.engines.base import EngineAdapter
from src.tools.render.engines.pandoc.docx_adapter import PandocDocxEngineAdapter
from src.tools.render.engines.pandoc.pdf_adapter import PandocPdfEngineAdapter

_TEMPLATES_ROOT = Path(__file__).parent / "templates"
_FILTERS_ROOT = Path(__file__).parent / "engines" / "pandoc" / "filters"


class EngineManifest(BaseModel):
    template: str | None = None
    reference_doc: str | None = None
    lua_filters: list[str] = Field(default_factory=list)


class StyleManifest(BaseModel):
    document_type: str
    style: str
    asset_roots: list[str] = Field(default_factory=list)
    engines: dict[str, EngineManifest]


def get_document_adapter(document_type: str):
    """Return the registered adapter for a document type."""
    adapters = {
        "cv": CVDocumentAdapter(),
        "letter": LetterDocumentAdapter(),
    }
    try:
        return adapters[document_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported document type '{document_type}'") from exc


def get_engine_adapter(engine: str) -> EngineAdapter:
    """Return the registered engine adapter."""
    engines: dict[str, EngineAdapter] = {
        "tex": PandocPdfEngineAdapter(),
        "docx": PandocDocxEngineAdapter(),
    }
    try:
        return engines[engine]
    except KeyError as exc:
        raise ValueError(f"Unsupported engine '{engine}'") from exc


def load_style_manifest(document_type: str, style: str) -> StyleManifest:
    """Load a style manifest from the root templates directory."""
    path = _TEMPLATES_ROOT / document_type / style / "manifest.json"
    if not path.exists():
        raise ValueError(f"Unknown style '{style}' for document type '{document_type}'")
    payload = json.loads(path.read_text())
    return StyleManifest.model_validate(payload)


def resolve_manifest_paths(
    manifest: StyleManifest, engine: str
) -> tuple[Path | None, Path | None, list[Path], list[Path]]:
    """Resolve template, reference, filter, and asset paths from a manifest."""
    engine_manifest = manifest.engines.get(engine)
    if engine_manifest is None:
        raise ValueError(f"Style '{manifest.style}' does not support engine '{engine}'")

    style_root = _TEMPLATES_ROOT / manifest.document_type / manifest.style
    template_path = (
        style_root / engine_manifest.template if engine_manifest.template else None
    )
    reference_doc = (
        style_root / engine_manifest.reference_doc
        if engine_manifest.reference_doc
        else None
    )
    lua_filters = [_FILTERS_ROOT / name for name in engine_manifest.lua_filters]
    asset_roots = [(style_root / asset).resolve() for asset in manifest.asset_roots]
    return template_path, reference_doc, lua_filters, asset_roots
