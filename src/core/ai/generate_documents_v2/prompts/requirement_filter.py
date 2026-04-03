"""Prompts for the requirement filter node (J2 -> J3 / JobDelta)."""

from __future__ import annotations

import json

from src.core.ai.generate_documents_v2.contracts.job import JobKG

FILTER_SYSTEM_PROMPT = """You are a strategic job application advisor.
Given a structured job knowledge graph, decide what to emphasize and what to deprioritize.

Rules:
- must_highlight_skills: list the 3-5 most critical technical skills the application MUST demonstrate
- ignored_requirements: list requirements that are clearly secondary or nice to have
- soft_vibe_requirements: list cultural or personality signals worth reflecting in tone
- logistics_flags: boolean flags - set relocation_relevant=true if location change is required and relevant to mention
- custom_instructions: any specific tactical note for this application (e.g. mention visa status)
- Be decisive. An application that tries to address everything emphasizes nothing.
"""


def build_filter_user_prompt(job_kg: JobKG) -> str:
    hard = [
        f"[{req.id}] {req.text} (priority={req.priority})"
        for req in job_kg.hard_requirements
    ]
    soft = [f"[{req.id}] {req.text}" for req in job_kg.soft_context]
    logistics_parts: list[str] = []

    if job_kg.logistics.location:
        logistics_parts.append(f"Location: {job_kg.logistics.location}")
    if job_kg.logistics.relocation:
        logistics_parts.append("Relocation offered")
    if job_kg.logistics.visa_sponsorship:
        logistics_parts.append("Visa sponsorship available")

    return f"""Analyze this job knowledge graph and produce a relevance delta.

HARD REQUIREMENTS:
{json.dumps(hard, indent=2)}

SOFT CONTEXT:
{json.dumps(soft, indent=2)}

LOGISTICS:
{chr(10).join(logistics_parts) if logistics_parts else "Not specified"}

COMPANY: {job_kg.company.name or "Unknown"}

Decide what to highlight, what to ignore, and any tactical flags for this application.
"""
