from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RenderInputState(BaseModel):
    source: str
    job_id: str

    @field_validator("source", "job_id")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("source and job_id must be non-empty")
        return cleaned


class RenderedDocumentRef(BaseModel):
    source_ref: str = Field(
        ..., description="Input markdown artifact relative to job root"
    )
    rendered_ref: str = Field(
        ..., description="Render-stage markdown artifact relative to job root"
    )
    sha256: str = Field(..., description="sha256 hash for rendered content")

    @field_validator("sha256")
    @classmethod
    def _validate_sha256_prefix(cls, value: str) -> str:
        if not value.startswith("sha256:"):
            raise ValueError("sha256 must start with 'sha256:'")
        return value


class RenderStateEnvelope(BaseModel):
    node: str = "render"
    source: str
    job_id: str
    generated_at: str
    documents: dict[str, RenderedDocumentRef]
