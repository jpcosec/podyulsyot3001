from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContactInfo:
    email: str
    phone: str
    address: str
    linkedin: str = ""
    github: str = ""


@dataclass
class EducationEntry:
    degree: str
    institution: str
    location: str
    start_date: str
    end_date: str
    specialization: str = ""
    equivalency_note: str = ""


@dataclass
class ExperienceEntry:
    role: str
    organization: str
    location: str
    start_date: str
    end_date: str
    achievements: list[str] = field(default_factory=list)


@dataclass
class PublicationEntry:
    year: int
    title: str
    venue: str
    url: str = ""


@dataclass
class LanguageEntry:
    name: str
    level: str
    note: str = ""


@dataclass
class CVModel:
    full_name: str
    tagline: str
    contact: ContactInfo
    summary: str
    education: list[EducationEntry]
    experience: list[ExperienceEntry]
    publications: list[PublicationEntry]
    languages: list[LanguageEntry]
    skills: dict[str, list[str]]

    @classmethod
    def from_profile(cls, profile: dict[str, Any]) -> "CVModel":
        owner = profile.get("owner", {})
        contact_data = owner.get("contact", {})
        addresses = contact_data.get("addresses", [])
        current_address = next((a for a in addresses if a.get("label") == "current"), {})
        links = owner.get("links", {})

        contact = ContactInfo(
            email=contact_data.get("email", ""),
            phone=contact_data.get("phone", ""),
            address=current_address.get("value", ""),
            linkedin=links.get("linkedin", ""),
            github=links.get("github", ""),
        )

        education = [
            EducationEntry(
                degree=e.get("degree", ""),
                institution=e.get("institution", ""),
                location=e.get("location", ""),
                start_date=e.get("start_date", ""),
                end_date=e.get("end_date", ""),
                specialization=e.get("specialization", ""),
                equivalency_note=e.get("equivalency_note", ""),
            )
            for e in profile.get("education", [])
        ]

        experience = [
            ExperienceEntry(
                role=e.get("role", ""),
                organization=e.get("organization", ""),
                location=e.get("location", ""),
                start_date=e.get("start_date", ""),
                end_date=e.get("end_date", ""),
                achievements=e.get("achievements", []),
            )
            for e in profile.get("experience", [])
        ]

        publications = [
            PublicationEntry(
                year=p.get("year", 0),
                title=p.get("title", ""),
                venue=p.get("venue", ""),
                url=p.get("url", ""),
            )
            for p in profile.get("publications", [])
        ]

        languages = [
            LanguageEntry(
                name=lang.get("name", ""),
                level=lang.get("level", ""),
                note=lang.get("note", ""),
            )
            for lang in profile.get("languages", [])
        ]

        return cls(
            full_name=owner.get("full_name", ""),
            tagline=owner.get("tagline", ""),
            contact=contact,
            summary=owner.get("professional_summary", ""),
            education=education,
            experience=experience,
            publications=publications,
            languages=languages,
            skills=profile.get("skills", {}),
        )
