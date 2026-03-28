"""Typed render request models."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RenderRequest(BaseModel):
    """Input request for a document render."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    document_type: Literal["cv", "letter"]
    engine: Literal["tex", "docx"] = "tex"
    style: str | None = None
    language: str = "en"
    source: str
    source_kind: Literal["direct", "job"] = "direct"
    job_id: str | None = None
    output_path: Path | None = None
    extra_vars: dict[str, str] = Field(default_factory=dict)

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        aliases = {
            "english": "en",
            "en-us": "en",
            "en-gb": "en",
            "spanish": "es",
            "es-es": "es",
            "german": "de",
            "de-de": "de",
        }
        return aliases.get(value.lower(), value.lower())
