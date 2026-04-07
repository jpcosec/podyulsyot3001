"""Prompts for the ingestion node (J1 -> J2 / JobKG)."""

from __future__ import annotations

import json
from typing import Any

INGESTION_SYSTEM_PROMPT = """You are a precise job-posting analyst.
Your task is to extract structured data from a raw job description.

Rules:
- Output audit-facing semantic content in English whenever possible.
- Preserve the original job title separately as job_title_original.
- Set job_title_english to an English rendering suitable for human auditing.
- Extract ONLY what is explicitly stated or strongly implied in the text.
- Separate hard technical requirements from soft cultural context.
- Assign realistic priority scores (1=low, 5=critical).
- Generate stable IDs: hard requirements as R01, R02...; soft as S01, S02...
- For logistics, extract location, remote policy, relocation, visa sponsorship only when mentioned.
- Prefer canonical ingest state over teaser/listing metadata when sources disagree.
- Do NOT invent requirements not present in the text.
"""


def build_ingestion_user_prompt(
    *,
    job_raw_text: str | None = None,
    job_bundle: dict[str, Any] | None = None,
) -> str:
    """Build the user prompt for ingestion from raw text or bundled artifacts."""
    if job_bundle:
        return _build_bundle_prompt(job_bundle)

    return f"""Extract the structured job knowledge graph from this job posting.

JOB POSTING:
{job_raw_text or ""}

Produce a JobKG with:
- source_language, job_title_original, job_title_english
- hard_requirements: technical skills, experience, certifications explicitly required
- soft_context: culture, collaboration, growth mentions
- logistics: location, remote/hybrid, contract type, relocation support, visa sponsorship
- company: company name, hiring department, contact person if mentioned
- salary_range: salary or pay-grade as stated (e.g. "EUR 70k–90k", "Grade IC4"); omit if not mentioned
"""


def _build_bundle_prompt(job_bundle: dict[str, Any]) -> str:
    state = _select_state_fields(job_bundle.get("state", {}))
    listing = _select_listing_fields(job_bundle.get("listing", {}))
    listing_case = _select_listing_case_fields(job_bundle.get("listing_case", {}))

    return f"""Extract the structured job knowledge graph from this bundled ingest payload.

Use the canonical state as the primary source of truth.
Use listing and listing_case only as supporting metadata and teaser context.

CANONICAL STATE JSON:
{json.dumps(state, ensure_ascii=True, indent=2)}

LISTING JSON:
{json.dumps(listing, ensure_ascii=True, indent=2)}

LISTING CASE JSON:
{json.dumps(listing_case, ensure_ascii=True, indent=2)}

Produce a JobKG with:
- source_language, job_title_original, job_title_english
- hard_requirements written in English for human auditability
- soft_context written in English for human auditability
- logistics normalized from the canonical state
- company metadata
- salary_range: salary or pay-grade from canonical state or teaser; omit if not mentioned

Important:
- Keep company names and original titles exact where possible.
- Do not paraphrase into English inside job_title_original.
- job_title_english should be short and audit-friendly.
"""


def _select_state_fields(state: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "job_title",
        "company_name",
        "location",
        "employment_type",
        "responsibilities",
        "requirements",
        "salary",
        "remote_policy",
        "benefits",
        "company_description",
        "company_industry",
        "company_size",
        "application_method",
        "application_instructions",
        "reference_number",
        "original_language",
    )
    return {key: state.get(key) for key in keys if state.get(key) not in (None, [], "")}


def _select_listing_fields(listing: dict[str, Any]) -> dict[str, Any]:
    keys = ("listing_data", "listing_snippet")
    return {
        key: listing.get(key) for key in keys if listing.get(key) not in (None, {}, "")
    }


def _select_listing_case_fields(listing_case: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "teaser_title",
        "teaser_company",
        "teaser_location",
        "teaser_salary",
        "teaser_employment_type",
        "teaser_text",
    )
    return {
        key: listing_case.get(key)
        for key in keys
        if listing_case.get(key) not in (None, "")
    }
