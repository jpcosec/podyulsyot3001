from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DraftedSection(BaseModel):
    section_id: str
    raw_markdown: str
    is_cohesive: bool = True
    word_count: int = 0

    @model_validator(mode="after")
    def _compute_word_count(self) -> "DraftedSection":
        if self.word_count == 0 and self.raw_markdown:
            self.word_count = len(self.raw_markdown.split())
        return self


class DraftedDocument(BaseModel):
    doc_type: Literal["cv", "letter", "email"]
    sections_md: dict[str, str] = Field(default_factory=dict)
    cohesion_score: float = Field(ge=0.0, le=1.0, default=1.0)
