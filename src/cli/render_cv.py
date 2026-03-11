"""Render a tailored CV PDF from profile data for a given job.

Usage:
    python -m src.cli.render_cv --source tu_berlin --job-id 201553
    python -m src.cli.render_cv --source tu_berlin --job-id 201553 --language english
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from src.core.tools.render.latex import compile_cv_pdf


_PROFILE_PATH = Path(
    "data/reference_data/profile/base_profile/profile_base_data.json"
)


def _build_context(profile: dict) -> dict: #TODO : Enforce order, deterministic code belongs in core.
    """Convert profile_base_data.json shape to LaTeX template context."""
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

    education = []
    for edu in profile.get("education", []):
        education.append({
            "degree": edu.get("degree", ""),
            "specialization": edu.get("specialization", ""),
            "institution": edu.get("institution", ""),
            "location": edu.get("location", ""),
            "start_date": edu.get("start_date", ""),
            "end_date": edu.get("end_date", ""),
            "equivalency_note": edu.get("equivalency_note", ""),
        })

    experience = []
    for exp in profile.get("experience", []):
        experience.append({
            "role": exp.get("role", ""),
            "organization": exp.get("organization", ""),
            "location": exp.get("location", ""),
            "start_date": exp.get("start_date", ""),
            "end_date": exp.get("end_date", ""),
            "achievements": exp.get("achievements", []),
        })

    raw_skills = profile.get("skills", {})
    skills = {k: v for k, v in raw_skills.items()}

    # Normalize optional fields — template uses StrictUndefined so all accessed keys must exist
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
        "skills": skills,
    }


def render_cv(source: str, job_id: str, language: str = "english") -> Path:
    profile = json.loads(_PROFILE_PATH.read_text())
    context = _build_context(profile)

    job_dir = Path(f"data/jobs/{source}/{job_id}")
    application_dir = job_dir / "application"
    application_dir.mkdir(parents=True, exist_ok=True)

    build_dir = job_dir / "render_build" / "cv"
    build_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = compile_cv_pdf(context, build_dir, language=language)

    dest = application_dir / "cv.pdf"
    shutil.copy(str(pdf_path), str(dest))
    print(f"CV written to {dest}")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Render tailored CV PDF for a job.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--language", default="english", choices=["english", "german", "spanish"])
    args = parser.parse_args()
    render_cv(args.source, args.job_id, args.language)


if __name__ == "__main__":
    main()
