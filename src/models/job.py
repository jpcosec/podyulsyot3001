from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    id: str
    text: str
    priority: Literal["must", "nice"] = "must"


class JobPosting(BaseModel):
    title: str
    reference_number: str = ""
    deadline: str = ""
    institution: str = ""
    department: str = ""
    location: str = ""
    contact_name: str = ""
    contact_email: str = ""
    requirements: list[JobRequirement]
    themes: list[str]
    responsibilities: list[str] = Field(default_factory=list)
    raw_text: str = ""

    @classmethod
    def from_summary_json(cls, data: dict) -> "JobPosting":
        """Build from scraper's summary.json output."""
        raw_requirements = data.get("requirements", [])
        requirements = [
            JobRequirement(id=f"R{index}", text=str(item), priority="must")
            for index, item in enumerate(raw_requirements, start=1)
            if str(item).strip()
        ]

        return cls(
            title=str(data.get("title", "")),
            reference_number=str(data.get("reference_number", "")),
            deadline=str(data.get("deadline", "")),
            institution=str(data.get("institution", "")),
            department=str(data.get("department", "")),
            location=str(data.get("location", "")),
            contact_name=str(data.get("contact_name", data.get("contact_person", ""))),
            contact_email=str(data.get("contact_email", "")),
            requirements=requirements,
            themes=[str(item) for item in data.get("themes", []) if str(item).strip()],
            responsibilities=[
                str(item)
                for item in data.get("responsibilities", [])
                if str(item).strip()
            ],
            raw_text=str(data.get("raw_text", "")),
        )
