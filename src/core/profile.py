"""Contracts and models for the candidate profile in schema-v0."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProfileOwner(BaseModel):
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
    role: str
    organization: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

class ProfileProject(BaseModel):
    name: str
    role: Optional[str] = None
    stack: List[str] = Field(default_factory=list)

class ProfilePublication(BaseModel):
    title: str
    venue: str
    year: Optional[int] = None
    url: Optional[str] = None

class ProfileLanguage(BaseModel):
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
