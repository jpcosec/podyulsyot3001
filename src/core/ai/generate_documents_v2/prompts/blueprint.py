"""Prompts for blueprint generation."""

from __future__ import annotations

import json

from src.core.ai.generate_documents_v2.contracts.job import JobDelta
from src.core.ai.generate_documents_v2.contracts.matching import MatchEdge
from src.core.ai.generate_documents_v2.contracts.profile import SectionMappingItem

BLUEPRINT_SYSTEM_PROMPT = """You are a macroplanning engine for job-application documents.

Rules:
- Build a concise, ordered blueprint.
- Use section IDs from the section mapping.
- logical_train_of_thought should contain fact-like IDs or evidence IDs in useful order.
- section_intent must be short, specific, and written in English.
"""


def build_blueprint_user_prompt(
    *,
    application_id: str,
    strategy_type: str,
    section_mapping: list[SectionMappingItem],
    job_delta: JobDelta,
    matches: list[MatchEdge],
    job_title: str | None = None,
    source: str | None = None,
) -> str:
    mapping_payload = [item.model_dump() for item in section_mapping]
    matches_payload = [item.model_dump() for item in matches]
    return f"""Build a GlobalBlueprint for this application.

APPLICATION ID: {application_id}
STRATEGY TYPE: {strategy_type}
JOB TITLE: {job_title or "Unknown"}
SOURCE PLATFORM: {source or "Unknown"}

SECTION MAPPING:
{json.dumps(mapping_payload, ensure_ascii=True, indent=2)}

JOB DELTA:
{job_delta.model_dump_json(indent=2)}

MATCH EDGES:
{json.dumps(matches_payload, ensure_ascii=True, indent=2)}
"""
