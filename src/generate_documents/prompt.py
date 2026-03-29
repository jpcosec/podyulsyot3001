"""Prompt templates and builders for tailored document generation."""

from __future__ import annotations

import json
from typing import Any

from jinja2 import Environment, StrictUndefined

SYSTEM_PROMPT = """# Role
You are a strict technical application writer for the German job market.
Your task is to produce JSON deltas for CV, motivation letter, and email using only the provided data.

# Hard constraints
1. Output must be valid JSON for the provided schema.
2. Use factual and concise English.
3. Do not invent organizations, projects, dates, tools, or claims.
4. `cv_injections[].experience_id` must match one id from `<candidate_base_cv>.experience`.
5. Keep `cv_summary` to at most 3 non-empty lines.
6. Keep `email_body` to at most 2 non-empty lines.

# Anti-fluff constraints
Avoid marketing tone and self-praise language.
Do not use these phrases: excellent, expert, passionate, perfect, ideal, highly skilled, incredible, proven track record, successful, driven, dynamic, enthusiastic.
If uncertain, prefer short factual wording over persuasive language.

# Motivation letter structure rules
1. `intro_paragraph`: who you are, exact role targeted, why applying now.
2. `core_argument_paragraph`: strongest evidence and outcomes aligned to role requirements.
3. `alignment_paragraph`: why this employer/company specifically (projects, domain, mission, product context).
4. `closing_paragraph`: availability, invite discussion, thank the recipient.

# Coherence rule
The core_argument_paragraph must narratively align with the technical facts in cv_injections.
"""

USER_TEMPLATE = """# 1. Candidate Base Profile
<candidate_base_cv>
{{ filtered_profile_json }}
</candidate_base_cv>

# 2. Validated Matches (Final State)
<validated_matches>
  <approved>
{% for match in approved_matches %}
  - Requirement ID: {{ match.requirement_id }}
    Requirement: {{ match.requirement_text }}
    Mapped Evidence ID: {{ match.evidence_ids | join(', ') }}
    Reasoning: {{ match.reasoning }}
{% endfor %}
  </approved>

  <human_patches>
{% for item in review_items %}
  {% if item.decision == 'request_regeneration' %}
  - Requirement ID: {{ item.requirement_id }}
    Human Note: "{{ item.note }}"
    Patch Evidence: {{ item.patch_evidence.model_dump_json() if item.patch_evidence else 'None' }}
  {% endif %}
{% endfor %}
  </human_patches>
</validated_matches>

# 3. Execution Instructions
Populate the JSON schema with these steps:
1. Write a factual `cv_summary` (max 3 lines) using validated matches.
2. Write `cv_injections` using only `experience_id` values that exist in candidate_base_cv.experience.
3. Generate motivation letter deltas (Subject, Intro, Core, Alignment, Closing).
4. Generate a concise `email_body` of max 2 lines.
"""

def build_generate_documents_prompt_input(
    *,
    profile_base: dict[str, Any],
    approved_matches: list[Any],
    review_items: list[Any],
) -> dict[str, Any]:
    """Prepare the Jinja2 variable dict for the generation user prompt.

    Strips empty and metadata-only fields from the profile to reduce token
    usage before serialising it to JSON.

    Args:
        profile_base: Candidate base profile dict loaded from disk.
        approved_matches: Enriched match dicts (requirement_id, evidence_ids,
            reasoning, requirement_text).
        review_items: Raw review payload items; used to surface human patches
            in the ``<human_patches>`` block.

    Returns:
        Dict with keys ``filtered_profile_json``, ``approved_matches``, and
        ``review_items`` ready to be passed to the Jinja2 USER_TEMPLATE.
    """
    
    # We strip empty fields from profile to save tokens
    filtered_profile = {
        k: v for k, v in profile_base.items() 
        if v and k not in ("cv_generation_context", "metadata")
    }

    return {
        "filtered_profile_json": json.dumps(filtered_profile, indent=2, ensure_ascii=False),
        "approved_matches": approved_matches,
        "review_items": review_items,
    }

def build_generate_documents_prompt(
    profile_base: dict[str, Any],
    approved_matches: list[Any],
    review_items: list[Any],
) -> str:
    """Render the Jinja2 USER_TEMPLATE into the final user prompt string.

    Args:
        profile_base: Candidate base profile dict loaded from disk.
        approved_matches: Enriched match dicts to populate the
            ``<validated_matches>`` block.
        review_items: Raw review payload items; patches surface in the
            ``<human_patches>`` block when decision is
            ``request_regeneration``.

    Returns:
        Rendered prompt string ready to be passed as the ``user`` message
        in a ``ChatPromptTemplate``.
    """
    env = Environment(undefined=StrictUndefined)
    template = env.from_string(USER_TEMPLATE)
    
    variables = build_generate_documents_prompt_input(
        profile_base=profile_base,
        approved_matches=approved_matches,
        review_items=review_items,
    )
    
    return template.render(**variables)
