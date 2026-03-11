# 1. Job Requirements (Job ID: {{ job_id }})
<job_requirements>
{% for req in requirements %}
- [{{ req.id }}] {{ req.text }} (Priority: {{ req.priority }})
{% endfor %}
</job_requirements>

# 2. Candidate Profile Evidence
<profile_evidence>
{% for ev in profile_evidence %}
- [{{ ev.id }}] {{ ev.description }}
{% endfor %}
</profile_evidence>

# 3. Matching Instructions
Map each requirement against available evidence.
1. Evaluate whether there is a clear mapping between requirement and profile evidence.
2. Compute `match_score` (`0.0` to `1.0`).
3. Write concise `reasoning` to justify the score. If there is a gap, state it explicitly.

{% if round_feedback is defined and round_feedback %}
# 4. Previous Iteration Feedback (Round {{ prev_round }})
<round_feedback>
{% for item in round_feedback %}
- Requirement [{{ item.req_id }}]: "{{ item.reviewer_note }}" (action: {{ item.action }})
{% if item.patch_evidence %}
  - Suggested patch evidence: [{{ item.patch_evidence.id }}] {{ item.patch_evidence.description }}
{% endif %}
{% endfor %}
</round_feedback>

Apply these required updates in the new matching output.
{% endif %}

# 5. Output Format
Return a `MatchEnvelope` object that includes:
- `matches` list (`req_id`, `match_score`, `evidence_id`, `reasoning`).
- `total_score` (weighted mean).
- `decision_recommendation` based on covered `must` requirements, using EXACTLY one of: `proceed`, `marginal`, `reject`.
- `summary_notes`.

All natural-language output fields must be in English.
