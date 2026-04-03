"""Central schema-v0 data manager for job artifacts and lifecycle metadata.

The data manager owns the data-plane only: job roots, artifact placement,
primitive reads/writes, and metadata lifecycle under ``data/jobs``. It must stay
domain-agnostic and therefore only deals in primitive values (dict, str, bytes)
plus its own internal metadata model.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")

JobStatus = Literal["active", "urgent", "archived", "discarded"]


class DataManagerError(Exception):
    """Base exception for schema-v0 data-plane errors."""


class JobMetadata(BaseModel):
    """Lifecycle metadata stored in ``meta.json`` for each job."""

    schema_version: str = Field(default="v0")
    status: JobStatus = Field(default="active")
    created_at: str
    updated_at: str


class DataManager:
    """Manage schema-v0 job metadata and primitive artifact IO under ``data/jobs``."""

    def __init__(self, jobs_root: str | Path = "data/jobs") -> None:
        self.jobs_root = Path(jobs_root)

    def _validated_segment(self, value: str, field: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{field} is required")
        if not _SEGMENT_RE.match(cleaned):
            raise ValueError(f"{field} contains unsupported characters: {value!r}")
        return cleaned

    def _safe_relative_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise ValueError("relative_path must not be absolute")
        if any(part == ".." for part in candidate.parts):
            raise ValueError("relative_path must not contain '..'")
        return candidate

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def job_root(self, source: str, job_id: str) -> Path:
        """Return the canonical filesystem root for one job.

        Args:
            source: Source name.
            job_id: Job identifier.

        Returns:
            The root directory for the job.
        """
        src = self._validated_segment(source, "source")
        jid = self._validated_segment(job_id, "job_id")
        return self.jobs_root / src / jid

    def source_root(self, source: str) -> Path:
        """Return the root directory containing jobs for one source."""
        src = self._validated_segment(source, "source")
        return self.jobs_root / src

    def node_root(self, source: str, job_id: str, node_name: str) -> Path:
        """Return the root directory for one node within a job."""
        node = self._validated_segment(node_name, "node_name")
        return self.job_root(source, job_id) / "nodes" / node

    def node_stage_dir(
        self,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
    ) -> Path:
        """Return the directory for one node stage within a job."""
        stage_name = self._validated_segment(stage, "stage")
        return self.node_root(source, job_id, node_name) / stage_name

    def artifact_path(
        self,
        *,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
    ) -> Path:
        """Return the canonical path for one artifact file."""
        file_name = self._validated_segment(filename, "filename")
        return self.node_stage_dir(source, job_id, node_name, stage) / file_name

    def artifact_exists(
        self,
        *,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
    ) -> bool:
        """Check whether a canonical artifact already exists."""
        return self.artifact_path(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        ).exists()

    def resolve_under_job(self, source: str, job_id: str, relative_path: str) -> Path:
        """Resolve a safe relative path under the job root.

        Args:
            source: Source name.
            job_id: Job identifier.
            relative_path: Relative path inside the job root.

        Returns:
            A resolved path guaranteed to stay under the job directory.
        """
        root = self.job_root(source, job_id).resolve()
        relative = self._safe_relative_path(relative_path)
        resolved = (root / relative).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("relative_path escapes job root")
        return resolved

    def read_json_path(self, path: str | Path) -> dict:
        """Read a JSON file from an arbitrary path."""
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def write_json_path(self, path: str | Path, data: dict) -> Path:
        """Write JSON content to an arbitrary path and return that path."""
        target = Path(path)
        self._write_json_path(target, data)
        return target

    def read_text_path(self, path: str | Path) -> str:
        """Read text content from an arbitrary path."""
        return Path(path).read_text(encoding="utf-8")

    def write_text_path(self, path: str | Path, content: str) -> Path:
        """Write text content to an arbitrary path and return that path."""
        target = Path(path)
        self._write_text_path(target, content)
        return target

    def read_bytes_path(self, path: str | Path) -> bytes:
        """Read bytes from an arbitrary path."""
        return Path(path).read_bytes()

    def ensure_dir(self, path: str | Path) -> Path:
        """Ensure a directory exists and return its path."""
        target = Path(path)
        target.mkdir(parents=True, exist_ok=True)
        return target

    def write_bytes_path(self, path: str | Path, content: bytes) -> Path:
        """Write bytes to an arbitrary path and return that path."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def sha256_path(self, path: str | Path) -> str:
        """Return a ``sha256:...`` digest for a file path."""
        digest = hashlib.sha256(self.read_bytes_path(path)).hexdigest()
        return f"sha256:{digest}"

    def ensure_job(self, source: str, job_id: str) -> JobMetadata:
        """Ensure a job root and metadata file exist.

        Args:
            source: Source name.
            job_id: Job identifier.

        Returns:
            The current job metadata after touching its timestamp.
        """
        root = self.job_root(source, job_id)
        root.mkdir(parents=True, exist_ok=True)
        meta_path = root / "meta.json"
        if meta_path.exists():
            metadata = JobMetadata.model_validate_json(
                meta_path.read_text(encoding="utf-8")
            )
            metadata.updated_at = self._timestamp()
            self._write_json_path(meta_path, metadata.model_dump())
            return metadata

        timestamp = self._timestamp()
        metadata = JobMetadata(created_at=timestamp, updated_at=timestamp)
        self._write_json_path(meta_path, metadata.model_dump())
        return metadata

    def get_job_metadata(self, source: str, job_id: str) -> JobMetadata:
        """Return lifecycle metadata for a job, creating it if needed."""
        meta_path = self.job_root(source, job_id) / "meta.json"
        if not meta_path.exists():
            return self.ensure_job(source, job_id)
        return JobMetadata.model_validate_json(meta_path.read_text(encoding="utf-8"))

    def update_job_status(
        self, source: str, job_id: str, status: JobStatus
    ) -> JobMetadata:
        """Update and persist the lifecycle status for a job."""
        metadata = self.get_job_metadata(source, job_id)
        metadata.status = status
        metadata.updated_at = self._timestamp()
        self._write_json_path(
            self.job_root(source, job_id) / "meta.json",
            metadata.model_dump(),
        )
        return metadata

    def write_json_artifact(
        self,
        *,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
        data: dict,
    ) -> Path:
        """Write a canonical JSON artifact under a job node stage."""
        self.ensure_job(source, job_id)
        path = self.artifact_path(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        self._write_json_path(path, data)
        self._touch_job(source, job_id)
        return path

    def read_json_artifact(
        self,
        *,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
    ) -> dict:
        """Read a canonical JSON artifact from a job node stage."""
        path = self.artifact_path(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def write_text_artifact(
        self,
        *,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
        content: str,
    ) -> Path:
        """Write a canonical text artifact under a job node stage."""
        self.ensure_job(source, job_id)
        path = self.artifact_path(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        self._write_text_path(path, content)
        self._touch_job(source, job_id)
        return path

    def read_text_artifact(
        self,
        *,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
    ) -> str:
        """Read a canonical text artifact from a job node stage."""
        path = self.artifact_path(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        return path.read_text(encoding="utf-8")

    def ingest_raw_job(
        self,
        *,
        source: str,
        job_id: str,
        payload: dict,
        content: str = "",
        metadata: dict | None = None,
        raw_html: str | None = None,
        cleaned_html: str | None = None,
        node_name: str = "ingest",
        stage: str = "proposed",
    ) -> dict[str, Path]:
        """Write the canonical raw ingest artifact bundle for one job.

        Args:
            source: Source name.
            job_id: Job identifier.
            payload: Canonical structured job payload.
            content: Optional markdown content extracted from the posting.
            metadata: Optional scrape metadata payload.
            raw_html: Optional raw HTML capture.
            cleaned_html: Optional cleaned HTML capture.
            node_name: Node name to write under.
            stage: Stage name to write under.

        Returns:
            Paths keyed by the artifacts that were written.
        """
        refs = {
            "state": self.write_json_artifact(
                source=source,
                job_id=job_id,
                node_name=node_name,
                stage=stage,
                filename="state.json",
                data=payload,
            )
        }
        if content:
            refs["content"] = self.write_text_artifact(
                source=source,
                job_id=job_id,
                node_name=node_name,
                stage=stage,
                filename="content.md",
                content=content,
            )
        if metadata is not None:
            refs["meta"] = self.write_json_artifact(
                source=source,
                job_id=job_id,
                node_name=node_name,
                stage=stage,
                filename="scrape_meta.json",
                data=metadata,
            )
        if raw_html is not None:
            refs["raw_html"] = self.write_text_artifact(
                source=source,
                job_id=job_id,
                node_name=node_name,
                stage=stage,
                filename="raw_page.html",
                content=raw_html,
            )
        if cleaned_html is not None:
            refs["cleaned_html"] = self.write_text_artifact(
                source=source,
                job_id=job_id,
                node_name=node_name,
                stage=stage,
                filename="cleaned_page.html",
                content=cleaned_html,
            )
        return refs

    def has_ingested_job(
        self,
        source: str,
        job_id: str,
        *,
        node_name: str = "ingest",
        stage: str = "proposed",
    ) -> bool:
        """Return whether the canonical ingest ``state.json`` exists for a job."""
        return self.artifact_exists(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename="state.json",
        )

    def write_bytes_artifact(
        self,
        *,
        source: str,
        job_id: str,
        node_name: str,
        stage: str,
        filename: str,
        content: bytes,
    ) -> Path:
        """Write a canonical bytes artifact under a job node stage."""
        self.ensure_job(source, job_id)
        path = self.artifact_path(
            source=source,
            job_id=job_id,
            node_name=node_name,
            stage=stage,
            filename=filename,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        self._touch_job(source, job_id)
        return path

    def _touch_job(self, source: str, job_id: str) -> None:
        metadata = self.get_job_metadata(source, job_id)
        metadata.updated_at = self._timestamp()
        self._write_json_path(
            self.job_root(source, job_id) / "meta.json", metadata.model_dump()
        )

    def _write_json_path(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _write_text_path(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
