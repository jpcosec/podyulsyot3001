"""Minimal language bundle models for the render coordinator."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LanguageBundle(BaseModel):
    """Typed language metadata used by the render coordinator."""

    code: str
    common: dict[str, str] = Field(default_factory=dict)
    documents: dict[str, dict[str, str]] = Field(default_factory=dict)

    def metadata_for(self, document_type: str, style: str) -> dict[str, str]:
        """Return merged language metadata for one document/style pair."""
        metadata = dict(self.common)
        metadata.update(self.documents.get(document_type, {}))
        metadata.setdefault("style", style)
        return metadata
