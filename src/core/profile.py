"""Contracts and models for the candidate profile in schema-v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.core.api_client import LangGraphAPIClient


class ProfileOwner(BaseModel):
    """Identity and contact information for the profile owner."""

    full_name: str
    preferred_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    nationality: Optional[str] = None
    contact: Dict[str, Any] = Field(default_factory=dict)
    links: Dict[str, str] = Field(default_factory=dict)
    legal_status: Dict[str, Any] = Field(default_factory=dict)
    professional_summary: Optional[str] = None
    tagline: Optional[str] = None


class ProfileEducation(BaseModel):
    """One education entry in the canonical profile."""

    degree: str
    institution: str
    specialization: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    level_reference: Optional[str] = None
    equivalency_note: Optional[str] = None
    grade: Optional[str] = None


class ProfileExperience(BaseModel):
    """One work experience entry in the canonical profile."""

    role: str
    organization: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class ProfileProject(BaseModel):
    """One project entry in the canonical profile."""

    name: str
    role: Optional[str] = None
    stack: List[str] = Field(default_factory=list)


class ProfilePublication(BaseModel):
    """One publication entry in the canonical profile."""

    title: str
    venue: str
    year: Optional[int] = None
    url: Optional[str] = None


class ProfileLanguage(BaseModel):
    """One language proficiency entry in the canonical profile."""

    name: str
    level: str
    note: Optional[str] = None


class ProfileBaseData(BaseModel):
    """Canonical structure of the master profile JSON."""

    snapshot_version: Optional[str] = None
    captured_on: Optional[str] = None
    owner: ProfileOwner
    education: List[ProfileEducation] = Field(default_factory=list)
    experience: List[ProfileExperience] = Field(default_factory=list)
    projects: List[ProfileProject] = Field(default_factory=list)
    publications: List[ProfilePublication] = Field(default_factory=list)
    languages: List[ProfileLanguage] = Field(default_factory=list)
    skills: Dict[str, List[str]] = Field(default_factory=dict)
    cv_generation_context: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class Profile:
    """Manager for the candidate's canonical profile data.

    Handles local persistence in 'data/reference_data' and synchronization
    with remote sources via the LangGraph API.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._data: Optional[ProfileBaseData] = None

    @property
    def data(self) -> ProfileBaseData:
        """Return the managed profile data, loading it if necessary."""
        if self._data is None:
            self.load()
        return self._data

    def load(self) -> ProfileBaseData:
        """Load profile data from the configured filesystem path."""
        if not self.path.exists():
            raise FileNotFoundError(f"Profile file not found at {self.path}")

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self._data = ProfileBaseData.model_validate(raw)
        return self._data

    def save(self) -> None:
        """Persist the current profile data back to disk."""
        if self._data is None:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            self._data.model_dump_json(indent=2, by_alias=True),
            encoding="utf-8",
        )

    async def refresh(self, client: LangGraphAPIClient, source: str) -> None:
        """Sync profile data from a remote source and update local storage."""
        from src.shared.log_tags import LogTag

        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"{LogTag.FAST} Refreshing profile from source: {source}")
        raw_data = await client.get_profile(source)

        # Validate before assigning
        new_data = ProfileBaseData.model_validate(raw_data)
        self._data = new_data
        self.save()
        logger.info(f"{LogTag.OK} Profile synced and saved to {self.path}")
