# 1. Candidate Base Profile
<candidate_base_cv>
{{ filtered_profile_json }}
</candidate_base_cv>

# 2. Validated Matches (Final State)
<validated_matches>
  <approved>
  {% for match in approved_matches %}
  - Requirement ID: {{ match.req_id }}
    Requirement: {{ match.req }}
    Mapped Evidence ID: {{ match.evidence_id }}
    Reasoning: {{ match.reasoning }}
  {% endfor %}
  </approved>

  <human_patches>
  {% for patch in human_patches %}
  - Requirement ID: {{ patch.req_id }}
    Requirement: {{ patch.req }}
    Human Note: "{{ patch.human_note }}"
    Current Evidence ID: {{ patch.evidence_id }}
  {% endfor %}
  </human_patches>
</validated_matches>

# 3. Execution Instructions
Populate the JSON schema with these steps:
1. Write a factual `cv_summary` (max 3 lines) using validated matches.
2. Write `cv_injections` using only `experience_id` values that exist in candidate_base_cv.experience.
3. Generate motivation letter deltas where `core_argument_paragraph` expands the same technical facts from `cv_injections`.
4. Generate a concise `email_body` of max 2 lines.
