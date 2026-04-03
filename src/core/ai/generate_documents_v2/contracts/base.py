"""Foundational traceability contracts shared across pipeline stages."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TextAnchor(BaseModel):
    """Locates an exact quote within a source document for audit trails."""

    document_id: str
    start_index: int = Field(ge=0)
    end_index: int = Field(ge=0)
    exact_quote: str

    @model_validator(mode="after")
    def _end_after_start(self) -> "TextAnchor":
        if self.end_index < self.start_index:
            raise ValueError("end_index must be >= start_index")
        return self


class IdeaFact(BaseModel):
    """Minimum traceable unit of information that can enter the pipeline."""

    id: str
    provenance_refs: list[str]
    core_content: str
    priority: int = Field(ge=1, le=5)
    status: Literal["keep", "hide", "merge"] = "keep"
    source_anchors: list[TextAnchor] = Field(default_factory=list)
