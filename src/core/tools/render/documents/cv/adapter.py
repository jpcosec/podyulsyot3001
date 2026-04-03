"""CV document adapter."""

from __future__ import annotations

from pathlib import Path

from src.core.data_manager import DataManager
from src.core.tools.render.documents.base import DocumentAdapter, DocumentPayload
from src.core.tools.render.request import RenderRequest
from src.core.tools.render.shared.paths import JobRenderPaths

_PROFILE_PATH = Path("data/reference_data/profile/base_profile/profile_base_data.json")


def _build_context(profile: dict) -> dict:
    owner = profile["owner"]
    contact = owner["contact"]
    address = contact["addresses"][0]["value"]
    city = address.split(",")[-2].strip() if "," in address else ""

    personal = {
        "full_name": owner["preferred_name"],
        "first_name": owner["preferred_name"].split()[0],
        "last_name": " ".join(owner["preferred_name"].split()[1:]),
        "email": contact["email"],
        "phone": contact["phone"],
        "address": address,
        "city": city,
        "tagline": profile.get("cv_generation_context", {}).get("tagline_seed", ""),
    }
    education = [
        {
            "degree": edu.get("degree", ""),
            "specialization": edu.get("specialization", ""),
            "institution": edu.get("institution", ""),
            "location": edu.get("location", ""),
            "start_date": edu.get("start_date", ""),
            "end_date": edu.get("end_date", ""),
            "equivalency_note": edu.get("equivalency_note", ""),
        }
        for edu in profile.get("education", [])
    ]
    experience = [
        {
            "role": exp.get("role", ""),
            "organization": exp.get("organization", ""),
            "location": exp.get("location", ""),
            "start_date": exp.get("start_date", ""),
            "end_date": exp.get("end_date", ""),
            "achievements": exp.get("achievements", []),
        }
        for exp in profile.get("experience", [])
    ]
    publications = [
        {**pub, "url": pub.get("url", "")} for pub in profile.get("publications", [])
    ]
    languages = [
        {**lang, "note": lang.get("note", "")} for lang in profile.get("languages", [])
    ]
    return {
        "personal": personal,
        "summary": profile.get("cv_generation_context", {}).get(
            "professional_summary_seed", ""
        ),
        "education": education,
        "experience": experience,
        "publications": publications,
        "languages": languages,
        "skills": dict(profile.get("skills", {})),
    }


class CVDocumentAdapter(DocumentAdapter):
    """Normalize CV inputs from Markdown or legacy JSON."""

    document_type = "cv"
    default_style = "classic"

    def resolve_job_source(self, request: RenderRequest, paths: JobRenderPaths) -> Path:
        """Resolve the best available CV source path for a render request.

        Args:
            request: Render request describing language and engine.
            paths: Precomputed render paths for the target job.

        Returns:
            The markdown CV path if present, otherwise the fallback profile path.
        """
        candidates = [
            paths.generate_dir / f"cv.{request.language}.md",
            paths.generate_dir / "cv.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return _PROFILE_PATH

    def build_payload(
        self, source_path: Path, request: RenderRequest
    ) -> DocumentPayload:
        """Build the render payload for a CV source.

        Args:
            source_path: Resolved source path for the CV.
            request: Render request describing engine and language.

        Returns:
            The normalized document payload consumed by the render coordinator.
        """
        if source_path.suffix == ".json":
            if request.engine != "tex":
                raise ValueError(
                    "Legacy JSON CV rendering only supports the 'tex' engine"
                )
            profile = DataManager().read_json_path(source_path)
            return DocumentPayload(
                document_type=self.document_type,
                source_kind="legacy_json",
                source_path=source_path,
                legacy_context=_build_context(profile),
            )

        return DocumentPayload(
            document_type=self.document_type,
            source_kind="markdown",
            source_path=source_path,
        )
