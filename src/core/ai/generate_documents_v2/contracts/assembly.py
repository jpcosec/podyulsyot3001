"""Assembly-stage contracts for generated Markdown documents and bundles."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class MarkdownDocument(BaseModel):
    """One assembled Markdown document with lightweight header/footer metadata."""

    doc_type: Literal["cv", "letter", "email"]
    header_data: dict[str, Any] = Field(default_factory=dict)
    body_markdown: str
    footer_data: dict[str, Any] = Field(default_factory=dict)


class FinalMarkdownBundle(BaseModel):
    """The complete Markdown outputs produced by the assembly stage."""

    cv_full_md: str
    letter_full_md: str
    email_body_md: str
    rendering_metadata: dict[str, Any] = Field(default_factory=dict)
