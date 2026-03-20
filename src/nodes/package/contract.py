from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PackageInputState(BaseModel):
    source: str
    job_id: str

    @field_validator("source", "job_id")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("source and job_id must be non-empty")
        return cleaned


class PackagedArtifact(BaseModel):
    path: str
    sha256: str = Field(..., description="sha256 hash for packaged artifact")

    @field_validator("sha256")
    @classmethod
    def _validate_sha256_prefix(cls, value: str) -> str:
        if not value.startswith("sha256:"):
            raise ValueError("sha256 must start with 'sha256:'")
        return value


class PackageManifest(BaseModel):
    node: str = "package"
    source: str
    job_id: str
    packaged_at: str
    render_state_ref: str
    artifacts: dict[str, PackagedArtifact]
