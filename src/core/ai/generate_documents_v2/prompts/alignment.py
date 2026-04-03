"""Prompts for profile-job alignment."""

from __future__ import annotations

import json

from src.core.ai.generate_documents_v2.contracts.job import JobKG
from src.core.ai.generate_documents_v2.contracts.profile import ProfileKG

ALIGNMENT_SYSTEM_PROMPT = """You are a precise application matching analyst.

Rules:
- Match profile evidence to job requirements conservatively.
- Prefer explicit evidence over vague similarity.
- Return concise English reasoning for auditability.
- Use requirement IDs from the JobKG exactly.
- Use profile evidence IDs from the ProfileKG exactly.
"""


def build_alignment_user_prompt(profile_kg: ProfileKG, job_kg: JobKG) -> str:
    """Build the user prompt for profile-to-job alignment."""
    profile_entries = [
        {
            "id": entry.id,
            "role": entry.role,
            "organization": entry.organization,
            "achievements": entry.achievements,
            "keywords": entry.keywords,
        }
        for entry in profile_kg.entries
    ]
    hard_requirements = [
        {"id": req.id, "text": req.text, "priority": req.priority}
        for req in job_kg.hard_requirements
    ]

    return f"""Match this profile against this job.

PROFILE SKILLS:
{json.dumps(profile_kg.skills, ensure_ascii=True, indent=2)}

PROFILE TRAITS:
{json.dumps(profile_kg.traits, ensure_ascii=True, indent=2)}

PROFILE ENTRIES:
{json.dumps(profile_entries, ensure_ascii=True, indent=2)}

JOB TITLE (EN): {job_kg.job_title_english or "Unknown"}

JOB HARD REQUIREMENTS:
{json.dumps(hard_requirements, ensure_ascii=True, indent=2)}
"""
