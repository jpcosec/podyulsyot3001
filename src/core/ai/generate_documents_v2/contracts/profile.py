"""Profile-side contracts: candidate knowledge graph and section strategy."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileEntry(BaseModel):
    """One experience or education item from the candidate profile."""

    id: str
    role: str = ""
    organization: str = ""
    achievements: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None


class EvidenceEdge(BaseModel):
    """Semantic relationship between two profile entries."""

    from_id: str
    to_id: str
    relation: str


class ProfileKG(BaseModel):
    """Persistent candidate knowledge graph (P1)."""

    entries: list[ProfileEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
    evidence_edges: list[EvidenceEdge] = Field(default_factory=list)


class SectionMappingItem(BaseModel):
    """Strategy rule for one document section (P2)."""

    section_id: str
    target_document: str
    country_context: str = "global"
    mandatory: bool = True
    default_priority: int = Field(ge=1, le=5, default=3)
    style_guideline: str = ""
    default_fact_ids: list[str] = Field(default_factory=list)
    target_tone: str | None = None
