"""JobState: Single source of truth for job paths, metadata, and artifact status."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from functools import cached_property
from pathlib import Path
from typing import Any


# Module-level path constants
PIPELINE_ROOT = Path(__file__).resolve().parents[2] / "data" / "pipelined_data"
REFERENCE_ROOT = Path(__file__).resolve().parents[2] / "data" / "reference_data"


class JobState:
    """Single source of truth for a job's paths, metadata, and artifact status."""

    ARCHIVE_DIR = "archive"

    STEP_OUTPUTS: dict[str, list[str]] = {
        "ingestion": [
            "raw/raw.html",
            "raw/source_text.md",
            "raw/extracted.json",
            "job.md",
        ],
        "matching": [
            "planning/match_proposal.md",
            "planning/reviewed_mapping.json",
            "planning/keywords.json",
        ],
        "motivation": [
            "planning/motivation_letter.md",
            "planning/motivation_letter.json",
        ],
        "cv_tailoring": ["planning/cv_tailoring.md", "cv/to_render.md"],
        "email_draft": ["planning/application_email.md"],
        "rendering": ["output/cv.pdf", "output/motivation_letter.pdf"],
        "packaging": ["output/Final_Application.pdf"],
    }

    STEP_ORDER = [
        "ingestion",
        "matching",
        "motivation",
        "cv_tailoring",
        "email_draft",
        "rendering",
        "packaging",
    ]

    def __init__(self, job_id: str, source: str = "tu_berlin"):
        """
        Initialize JobState for a job.

        Args:
            job_id: The numeric job ID (e.g., "201084")
            source: The source/company name (default: "tu_berlin")

        Raises:
            ValueError: If the job is archived
        """
        self.job_id = job_id
        self.source = source
        self._source_root = PIPELINE_ROOT / source
        self._job_dir = self._source_root / job_id

        if self.is_archived:
            raise ValueError(
                f"Job {job_id} is archived and cannot be operated on. "
                f"Found at: {self._job_dir}"
            )

    # ── Paths ──

    @property
    def job_dir(self) -> Path:
        """Return the job's root directory."""
        return self._job_dir

    def artifact_path(self, relative: str) -> Path:
        """
        Return the absolute path to a job artifact.

        Args:
            relative: Relative path within job_dir (e.g., "planning/cv_tailoring.md")

        Returns:
            Absolute Path to the artifact
        """
        return self._job_dir / relative

    # ── Metadata ──

    @cached_property
    def metadata(self) -> dict[str, Any]:
        """
        Load metadata from raw/extracted.json.

        Returns an empty dict if the file doesn't exist yet (e.g., before ingestion).
        """
        path = self.artifact_path("raw/extracted.json")
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    @property
    def deadline(self) -> date | None:
        """
        Parse and return the deadline as a date object.

        Handles ISO 8601 formats: "2026-03-06" or "2026-03-06T14:30:00Z".
        Returns None if deadline is missing or unparseable.
        """
        deadline_str = self.metadata.get("deadline")
        if not deadline_str:
            return None

        try:
            # Try parsing as ISO 8601 (with or without time)
            if "T" in deadline_str:
                return datetime.fromisoformat(deadline_str.replace("Z", "+00:00")).date()
            else:
                return datetime.strptime(deadline_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    @property
    def status(self) -> str:
        """Return the job status from metadata (e.g., 'open', 'archived', etc.)."""
        return self.metadata.get("status", "unknown")

    @property
    def is_archived(self) -> bool:
        """Check if job_dir is in an archive subdirectory."""
        return self.ARCHIVE_DIR in self._job_dir.parts

    # ── Step tracking ──

    def step_complete(self, step: str) -> bool:
        """
        Check if a step has completed (all its outputs exist).

        Args:
            step: Step name (e.g., "ingestion", "matching")

        Returns:
            True if all outputs for the step exist, False otherwise
        """
        if step not in self.STEP_OUTPUTS:
            return False

        outputs = self.STEP_OUTPUTS[step]
        return all(self.artifact_path(output).exists() for output in outputs)

    def pending_steps(self) -> list[str]:
        """Return list of incomplete steps (in order)."""
        return [step for step in self.STEP_ORDER if not self.step_complete(step)]

    def completed_steps(self) -> list[str]:
        """Return list of completed steps (in order)."""
        return [step for step in self.STEP_ORDER if self.step_complete(step)]

    def next_step(self) -> str | None:
        """Return the first incomplete step, or None if all steps are done."""
        pending = self.pending_steps()
        return pending[0] if pending else None

    # ── Artifact I/O ──

    def read_artifact(self, relative: str) -> str:
        """
        Read a text artifact as a string.

        Args:
            relative: Relative path within job_dir

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If artifact doesn't exist
        """
        path = self.artifact_path(relative)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_artifact(self, relative: str, content: str) -> Path:
        """
        Write a text artifact.

        Args:
            relative: Relative path within job_dir
            content: String content to write

        Returns:
            Path to the written artifact

        Creates parent directories if needed.
        """
        path = self.artifact_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def read_json_artifact(self, relative: str) -> dict[str, Any]:
        """
        Read a JSON artifact.

        Args:
            relative: Relative path within job_dir

        Returns:
            Parsed JSON as dict

        Raises:
            FileNotFoundError: If artifact doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        path = self.artifact_path(relative)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json_artifact(self, relative: str, data: dict[str, Any]) -> Path:
        """
        Write a JSON artifact.

        Args:
            relative: Relative path within job_dir
            data: Dict to serialize as JSON

        Returns:
            Path to the written artifact

        Creates parent directories if needed.
        """
        path = self.artifact_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    # ── Lifecycle ──

    def archive(self) -> None:
        """
        Move this job to the archive directory.

        After archiving, the job is no longer accessible via normal queries.
        Archives the job_dir to PIPELINE_ROOT / source / archive / job_id.
        """
        archive_root = self._source_root / self.ARCHIVE_DIR
        archive_root.mkdir(parents=True, exist_ok=True)
        archive_dest = archive_root / self.job_id

        if archive_dest.exists():
            raise FileExistsError(f"Archive destination already exists: {archive_dest}")

        self._job_dir.rename(archive_dest)

    # ── Class-level queries ──

    @classmethod
    def list_open_jobs(cls, source: str = "tu_berlin") -> list[JobState]:
        """
        List all open (non-archived) jobs for a source.

        Args:
            source: Source name (default: "tu_berlin")

        Returns:
            List of JobState instances for open jobs
        """
        source_root = PIPELINE_ROOT / source
        if not source_root.exists():
            return []

        open_jobs = []
        for item in source_root.iterdir():
            if item.is_dir() and item.name != cls.ARCHIVE_DIR and item.name.isdigit():
                try:
                    open_jobs.append(cls(item.name, source=source))
                except ValueError:
                    # Skip archived jobs (constructor raises ValueError)
                    pass

        return sorted(open_jobs, key=lambda j: j.job_id)

    @classmethod
    def list_expiring(cls, days: int, source: str = "tu_berlin") -> list[JobState]:
        """
        List jobs with deadline within the next N days.

        Args:
            days: Number of days to look ahead
            source: Source name (default: "tu_berlin")

        Returns:
            List of JobState instances, sorted by deadline
        """
        from datetime import timedelta

        cutoff = date.today() + timedelta(days=days)
        open_jobs = cls.list_open_jobs(source=source)

        expiring = [
            job
            for job in open_jobs
            if job.deadline is not None and job.deadline <= cutoff
        ]
        return sorted(expiring, key=lambda j: j.deadline or date.max)

    @classmethod
    def list_expired(cls, source: str = "tu_berlin") -> list[JobState]:
        """
        List jobs past their deadline.

        Args:
            source: Source name (default: "tu_berlin")

        Returns:
            List of JobState instances, sorted by deadline (oldest first)
        """
        open_jobs = cls.list_open_jobs(source=source)
        expired = [job for job in open_jobs if job.deadline and job.deadline < date.today()]
        return sorted(expired, key=lambda j: j.deadline or date.max)

    @classmethod
    def list_by_keyword(cls, keyword: str, source: str = "tu_berlin") -> list[JobState]:
        """
        List jobs matching a keyword.

        Searches for the keyword in planning/keywords.json (from the matching step).
        If that file doesn't exist, the job is skipped.

        Args:
            keyword: Keyword to search for
            source: Source name (default: "tu_berlin")

        Returns:
            List of JobState instances with matching keywords
        """
        open_jobs = cls.list_open_jobs(source=source)
        matching_jobs = []

        for job in open_jobs:
            try:
                keywords_data = job.read_json_artifact("planning/keywords.json")
                keywords_list = keywords_data.get("keywords", [])
                if keyword.lower() in (kw.lower() for kw in keywords_list):
                    matching_jobs.append(job)
            except (FileNotFoundError, json.JSONDecodeError):
                # Skip jobs that don't have keywords.json yet
                pass

        return matching_jobs
