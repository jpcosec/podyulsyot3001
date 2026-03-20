# Artifact Schemas and Structure

> Status note (2026-03-20): this document is now primarily target-state/schema-design guidance. It should not be treated as an exact description of current runtime artifacts. For current runtime artifact behavior, use `docs/reference/data_management_actual_state.md` and `docs/graph/node_io_matrix.md`.


Related references:

- `docs/graph/nodes_summary.md`
- `docs/graph/node_io_matrix.md`
- `docs/reference/document_glossary.md`

## Design rule

## Authority scope

- Canonical owner for artifact paths, artifact schema contracts, and format split (JSON/Markdown/YAML).
- Not the canonical source for graph routing policy.

Use this format split consistently:

- **JSON** = truth / state / machine contract.
- **Markdown** = review surface or render content.
- **YAML** = distilled active rules / config.

This single rule keeps the pipeline semantically clean: JSON is what the system trusts, markdown is what the human edits, and YAML is what persists as reusable knowledge.

## Artifact inventory

The pipeline produces 17 primary artifact types across its lifecycle. Each has a clear purpose, owner stage, format, and schema.

All paths below are relative to the job workspace root:

`data/jobs/<source>/<job_id>/`

---

## 1. `profile/profile_base_data.json`

Purpose: canonical profile knowledge base. Long-lived source of truth for personal/professional data.

Owner: profile ingestion / profile management (external to per-job pipeline).

```json
{
  "snapshot_version": "1.0",
  "captured_on": "YYYY-MM-DD",
  "source": {
    "external_root": "...",
    "primary_profile_file": "..."
  },
  "owner": {
    "full_name": "...",
    "preferred_name": "...",
    "birth_date": "YYYY-MM-DD",
    "nationality": "...",
    "contact": {
      "email": "...",
      "phone": "...",
      "addresses": [
        { "label": "current", "value": "..." }
      ]
    },
    "links": {
      "linkedin": "...",
      "github": "..."
    },
    "legal_status": {
      "visa_type": "...",
      "visa_status": "...",
      "work_permission_germany": true
    },
    "professional_summary": "...",
    "tagline": "..."
  },
  "education": [],
  "experience": [],
  "projects": [],
  "publications": [],
  "languages": [],
  "skills": {}
}
```

Rules:

- Keep this document factual only.
- Do not store application-specific positioning here.
- Do not inject temporary narrative edits into this file.

---

## 2. `nodes/extract_understand/proposed/state.json`

Purpose: structured interpretation of the job posting. Stable job-side semantic state.

Owner: `extract_understand`

```json
{
  "job_id": "201397",
  "source_url": "https://...",
  "captured_at": "2026-03-03T13:44:11Z",
  "job": {
    "title": "...",
    "reference_number": "...",
    "institution": "...",
    "department": "...",
    "location": "...",
    "deadline": "YYYY-MM-DD",
    "contact_name": "...",
    "contact_email": "..."
  },
  "requirements": [
    {
      "id": "R1",
      "text": "...",
      "priority": "must"
    }
  ],
  "themes": [],
  "responsibilities": [],
  "constraints": {
    "application_mode": "email_single_pdf",
    "language": ["English", "German"],
    "doctorate_possible": true
  },
  "signals": {
    "academic_level": "high",
    "preferred_orientation": ["empirical_research", "cognitive_science"],
    "risk_areas": ["EEG collection", "eye tracking collection"]
  },
  "raw_text_ref": "raw/source_text.md"
}
```

Rules:

- Keep this job-only.
- Avoid mixing profile-side interpretation here.

---

## 3. `nodes/match/proposed/state.json`

Purpose: machine-readable requirement-to-evidence mapping state.

Owner: `match`

```json
{
  "schema_version": "1.0",
  "job_id": "201397",
  "generated_at": "2026-03-03T13:44:11Z",
  "inputs": {
    "job_understanding_ref": "nodes/extract_understand/approved/state.json",
    "profile_ref": "profile/profile_base_data.json",
    "feedback_refs": ["feedback/active_memory.yaml"]
  },
  "job": {
    "title": "...",
    "reference_number": "...",
    "deadline": "YYYY-MM-DD",
    "institution": "...",
    "department": "...",
    "location": "...",
    "contact_name": "...",
    "contact_email": "...",
    "requirements": [],
    "themes": [],
    "responsibilities": []
  },
  "evidence_items": [
    {
      "id": "P_EXP_01",
      "type": "role|project|publication|education|skill|coursework|summary_line|other",
      "text": "...",
      "source_ref": "profile.experience[0].achievements[0]"
    }
  ],
  "mapping": [
    {
      "req_id": "R1",
      "priority": "must",
      "coverage": "full|partial|none",
      "evidence_ids": ["P_EDU_04", "P_EXP_01"],
      "notes": "...",
      "risk_flags": ["degree_domain_gap"],
      "forbidden_claims": [],
      "match_score": 0.68
    }
  ],
  "proposed_claims": [
    {
      "req_id": "R1",
      "claim": "...",
      "confidence": "low|moderate|high",
      "claim_type": "direct|bridging|adjacent",
      "supported_by_evidence_ids": ["P_EDU_04"]
    }
  ],
  "gaps": [
    {
      "req_id": "R4",
      "gap_type": "missing_direct_evidence",
      "notes": "No direct EEG collection experience."
    }
  ],
  "render": {
    "ordering": ["header", "summary", "education", "experience", "publications", "skills", "languages"],
    "style_rules": {
      "one_column": true,
      "no_tables": true,
      "no_icons": true
    }
  }
}
```

Rules:

- Owned by the matcher. Later stages reference it, not overwrite it.

---

## 4. `nodes/match/proposed/view.md`

Purpose: human review surface for matching. Editable requirement-by-requirement proposal.

Owner: `match` (generated by `sync_json_md`)

```markdown
---
schema_version: "1.0"
doc_type: "match_proposal"
status: "proposed"
job_id: "201397"
generated_at: "2026-03-03T13:44:11Z"
source_state_ref: "nodes/match/proposed/state.json"
profile_ref: "profile/profile_base_data.json"
job_ref: "nodes/extract_understand/approved/state.json"
review_round: 0
---

# Match Proposal: <job title>

## Review Instructions
- Approve when the claim is accurate and strategically useful.
- Edit when the claim is directionally right but needs refinement.
- Reject when the claim should not be used.
- Use Notes for rationale.

## Requirements Mapping

### R1: <requirement text> [FULL|PARTIAL|NONE]
Priority: must|nice
Evidence IDs: P_EDU_04, P_EXP_01
Evidence Summary: ...
Proposed Claim: ...
Confidence: moderate
Risk Flags: ...
Forbidden Claims: ...
Decision: [ ] approve  [ ] request_regeneration  [ ] reject
Notes:

## Gaps
...

## Strategic Notes
...
```

Rules:

- Intentionally editable; not validated truth.
- Review decisions are parsed into `review/decision.json`.

---

## 5. `nodes/review_match/approved/state.json`

Purpose: validated post-review matching state. Main downstream source of truth after human review.

Owner: `review_match`

```json
{
  "schema_version": "1.0",
  "doc_type": "reviewed_mapping",
  "job_id": "201397",
  "reviewed_at": "2026-03-03T15:00:00Z",
  "source_match_proposal_ref": "nodes/match/proposed/state.json",
  "decisions": [
    {
      "req_id": "R1",
      "requirement_text": "...",
      "initial_coverage": "partial",
      "final_decision": "approve|request_regeneration|reject",
      "approved_claim": "...",
      "reviewer_notes": "...",
      "reusable_feedback": true,
      "confidence_after_review": "moderate",
      "forbidden_claims": []
    }
  ],
  "gaps": [
    {
      "req_id": "R4",
      "status": "accepted_gap|unresolved_gap|rejected_requirement",
      "phrasing_strategy": "state processing experience only"
    }
  ],
  "summary": {
    "top_strengths": [],
    "main_risks": [],
    "positioning_direction": "..."
  }
}
```

Rules:

- First validated semantic state for downstream generators.

---

## 6. `nodes/build_application_context/proposed/state.json`

Purpose: shared grounded context for letter, CV, and email generation.

Owner: `build_application_context`

```json
{
  "schema_version": "1.0",
  "doc_type": "application_context",
  "job_id": "201397",
  "generated_at": "2026-03-03T15:10:00Z",
  "sources": {
    "reviewed_mapping_ref": "nodes/review_match/approved/state.json",
    "profile_ref": "profile/profile_base_data.json",
    "job_ref": "nodes/extract_understand/approved/state.json"
  },
  "positioning": {
    "target_role_type": "phd_research_assistant",
    "primary_narrative": "...",
    "secondary_narratives": [],
    "tone": ["academic", "precise", "truthful"],
    "forbidden_claims": [
      "Do not imply direct EEG data collection experience."
    ]
  },
  "approved_strengths": [
    {
      "requirement": "...",
      "approved_claim": "...",
      "evidence_refs": ["P_EXP_01"]
    }
  ],
  "bridging_claims": [
    {
      "requirement": "...",
      "claim": "...",
      "safe_framing": "..."
    }
  ],
  "accepted_gaps": [
    {
      "requirement": "...",
      "safe_handling": "..."
    }
  ],
  "target_emphasis": {
    "letter": [],
    "cv": [],
    "email": []
  },
  "evidence_priority_order": []
}
```

Rules:

- This is the main input for all downstream generation.
- Downstream generators must not reinterpret the job independently.

---

## 7. `nodes/generate_motivation_letter/proposed/state.json`

Purpose: structured draft state of the motivation letter.

Owner: `generate_motivation_letter`

```json
{
  "schema_version": "1.0",
  "doc_type": "motivation_letter_draft_state",
  "job_id": "201397",
  "generated_at": "2026-03-03T15:20:00Z",
  "application_context_ref": "nodes/build_application_context/approved/state.json",
  "subject": "...",
  "salutation": "...",
  "fit_signals": [
    {
      "requirement": "...",
      "evidence": "...",
      "coverage": "full|partial"
    }
  ],
  "risk_notes": [],
  "section_rationale": {
    "opening": "...",
    "fit_summary": "...",
    "research_alignment": "...",
    "closing": "..."
  },
  "letter_markdown_ref": "nodes/generate_motivation_letter/proposed/letter.md"
}
```

## 8. `nodes/generate_motivation_letter/proposed/letter.md`

Purpose: first reviewable letter draft.

Owner: `generate_motivation_letter`

```markdown
---
schema_version: "1.0"
doc_type: "motivation_letter_draft"
status: "pre_review"
job_id: "201397"
generated_at: "2026-03-03T15:20:00Z"
application_context_ref: "nodes/build_application_context/approved/state.json"
language: "en"
---

[City, Date]

<Recipient Name>
<Recipient Unit>
<Institution>

Subject: Application for <reference / title>

Dear <Recipient>,

<paragraph 1: role-specific opening and motivation>

<paragraph 2: strongest validated fit>

<paragraph 3: research alignment / methods / domain connection>

<paragraph 4: closing, logistics, availability, attachments>

Sincerely,

<Full Name>
<City>
<Email>
<Phone>
```

Rules:

- Keep it human-readable and editable.
- Key constraints must also be traceable in the JSON state.

---

## 9. `nodes/review_motivation_letter/approved/state.json`

Purpose: structured reviewed state of the motivation letter.

Owner: `review_motivation_letter`

```json
{
  "schema_version": "1.0",
  "doc_type": "motivation_letter_reviewed",
  "job_id": "201397",
  "reviewed_at": "2026-03-03T16:00:00Z",
  "source_draft_ref": "nodes/generate_motivation_letter/proposed/state.json",
  "final_markdown_ref": "nodes/review_motivation_letter/approved/letter.md",
  "sections": {
    "opening": "...",
    "fit_summary": "...",
    "research_alignment": "...",
    "closing": "..."
  },
  "validated_claims": [],
  "removed_claims": [],
  "style_rules_confirmed": [
    "avoid overstating domain fit",
    "keep tone academic"
  ],
  "downstream_guidance": {
    "cv_emphasis": [],
    "email_tone": "formal_concise"
  }
}
```

Rules:

- The reviewed motivation letter influences CV and email generation.
- This stage is a strategic alignment update, not just a document edit.

---

## 10. `nodes/tailor_cv/proposed/state.json`

Purpose: CV adaptation decisions and render-ready content reference.

Owner: `tailor_cv`

The tailoring notes are stored as `nodes/tailor_cv/proposed/view.md`:

```markdown
---
schema_version: "1.0"
doc_type: "cv_tailoring_notes"
status: "generated"
job_id: "201397"
generated_at: "2026-03-03T16:10:00Z"
application_context_ref: "nodes/build_application_context/approved/state.json"
motivation_review_ref: "nodes/review_motivation_letter/approved/state.json"
---

# CV Tailoring Notes

## Target Emphasis
- ...

## De-emphasized Areas
- ...

## Ordering Decisions
- ...

## Risk Controls
- ...
```

## 11. `nodes/tailor_cv/proposed/to_render.md`

Purpose: reviewer-facing CV content draft before final approval.

Owner: `tailor_cv`

```markdown
---
schema_version: "1.0"
doc_type: "cv_render_input"
status: "final_content"
job_id: "201397"
generated_at: "2026-03-03T16:15:00Z"
application_context_ref: "nodes/build_application_context/approved/state.json"
tailoring_notes_ref: "nodes/tailor_cv/proposed/view.md"
language: "en"
render_profile: "academic_phd"
---

# <Full Name>

## Header
- ...

## Summary
...

## Research Experience
...

## Industry Experience
...

## Education
...

## Publications
...

## Skills
...

## Languages
...
```

Rules:

- Keep it content-only.
- Avoid review checkboxes or editorial comments in this file.
- This draft must pass `review_cv` before becoming approved CV content.

---

## 12. `nodes/review_cv/approved/state.json`

Purpose: validated reviewed CV state for downstream consumers.

Owner: `review_cv`

```json
{
  "schema_version": "1.0",
  "doc_type": "cv_reviewed",
  "job_id": "201397",
  "reviewed_at": "2026-03-03T16:25:00Z",
  "source_draft_ref": "nodes/tailor_cv/proposed/state.json",
  "final_markdown_ref": "nodes/review_cv/approved/to_render.md",
  "decision": "approve|request_regeneration|reject",
  "reviewer_notes": "...",
  "downstream_guidance": {
    "email_alignment": "...",
    "render_constraints": ["..."]
  }
}
```

---

## 13. `nodes/draft_email/proposed/state.json`

Purpose: application email draft state.

Owner: `draft_email`

```json
{
  "schema_version": "1.0",
  "doc_type": "application_email_state",
  "job_id": "201397",
  "generated_at": "2026-03-03T16:20:00Z",
  "to": "...",
  "subject": "...",
  "salutation": "...",
  "body": "...",
  "closing": "Best regards,",
  "sender_name": "...",
  "sender_email": "...",
  "sender_phone": "..."
}
```

## 14. `nodes/draft_email/proposed/application_email.md`

Purpose: final human-readable email draft.

Owner: `draft_email`

```markdown
---
schema_version: "1.0"
doc_type: "application_email"
status: "generated"
job_id: "201397"
generated_at: "2026-03-03T16:20:00Z"
application_context_ref: "nodes/build_application_context/approved/state.json"
motivation_review_ref: "nodes/review_motivation_letter/approved/state.json"
cv_review_ref: "nodes/review_cv/approved/state.json"
language: "en"
recipient_name: "..."
recipient_email: "..."
subject_line: "..."
---

Subject: Application for <reference / title>

Dear <recipient>,

<body: 2 short paragraphs, 60-110 words>

Best regards,
<sender name>
<sender email>
<sender phone>
```

---

## 15. `nodes/review_email/approved/state.json`

Purpose: validated reviewed email state used for final delivery.

Owner: `review_email`

```json
{
  "schema_version": "1.0",
  "doc_type": "application_email_reviewed",
  "job_id": "201397",
  "reviewed_at": "2026-03-03T16:30:00Z",
  "source_draft_ref": "nodes/draft_email/proposed/state.json",
  "final_markdown_ref": "nodes/review_email/approved/application_email.md",
  "decision": "approve|request_regeneration|reject",
  "reviewer_notes": "..."
}
```

---

## 16. `meta/provenance.json` (shared schema)

Purpose: trace metadata for every approved artifact.

Used by: all reviewable nodes, stored at `nodes/<node>/meta/provenance.json`.

```json
{
  "artifact_id": "...",
  "node": "...",
  "job_id": "...",
  "run_id": "...",
  "produced_at": "ISO-8601",
  "contract_version": "1.0",
  "producer": "...",
  "inputs": [
    {
      "path": "...",
      "sha256": "...",
      "role": "..."
    }
  ],
  "review_decision_ref": "nodes/<node>/review/decision.json",
  "code_ref": "git:<commit_hash>",
  "prompt_ref": "src/ai/nodes/<node>/prompt/system.md",
  "prompt_version": "1.0",
  "model_ref": "provider/model_id"
}
```

Rules:

- Artifact is not considered approved if provenance block is missing or hash references cannot be resolved.
- `prompt_ref`, `prompt_version`, and `model_ref` apply only to LLM nodes.

---

## 17. `review/decision.md` and `review/decision.json` (shared structure)

Purpose: human review decision surface and its parsed representation.

Used by: all reviewable nodes, stored at `nodes/<node>/review/`.

`decision.md` structure:

```markdown
---
source_state_hash: "<sha256 of proposed/state.json>"
node: "<node_name>"
job_id: "<job_id>"
round: 1
---

# Review Decision: <node display name>

## <block_id>: <block label>

Decision: [ ] approve  [ ] request_regeneration  [ ] reject

Notes:
```

`decision.json` structure:

```json
{
  "node": "...",
  "job_id": "...",
  "round": 1,
  "source_state_hash": "...",
  "decisions": [
    {
      "block_id": "...",
      "decision": "approve|request_regeneration|reject",
      "notes": "...",
      "reusable_feedback": false
    }
  ],
  "updated_at": "ISO-8601"
}
```

Rules:

- `source_state_hash` must match the latest `proposed/state.json`. Mismatch = stale, parser rejects.
- Exactly one decision per block. Multiple or zero = parser error.
- See `docs/business_rules/sync_json_md.md` for the full parsing contract.
- See `docs/business_rules/claim_admissibility_and_policy.md` for review directive format.

---

## Supplemental feedback artifacts

Feedback artifacts live outside the per-node structure:

- `feedback/events/<stage>/<timestamp>.json`: per-event structured feedback.
- `feedback/active_memory.yaml`: distilled reusable rules for prompt injection.
- `feedback/conflicts.yaml`: explicit conflicts requiring human resolution.

See `docs/business_rules/feedback_memory.md` for full schemas.

---

## Supplemental output artifacts

Final rendered deliverables:

- `final/cv.pdf`
- `final/motivation_letter.pdf`
- `final/Final_Application.pdf`
- `final/manifest.json`
- Optional: `final/application_email.txt`, `final/application_bundle.zip`

---

## Summary: artifact role map

| # | Artifact | Role | Format |
|---|----------|------|--------|
| 1 | `profile/profile_base_data.json` | Canonical profile KB | JSON |
| 2 | `nodes/extract_understand/.../state.json` | Job understanding | JSON |
| 3 | `nodes/match/.../state.json` | Matching state | JSON |
| 4 | `nodes/match/.../view.md` | Match review surface | Markdown |
| 5 | `nodes/review_match/.../state.json` | Reviewed mapping | JSON |
| 6 | `nodes/build_application_context/.../state.json` | Application context | JSON |
| 7 | `nodes/generate_motivation_letter/.../state.json` | Letter draft state | JSON |
| 8 | `nodes/generate_motivation_letter/.../letter.md` | Letter draft | Markdown |
| 9 | `nodes/review_motivation_letter/.../state.json` | Reviewed letter state | JSON |
| 10 | `nodes/tailor_cv/.../view.md` | CV tailoring notes | Markdown |
| 11 | `nodes/tailor_cv/.../to_render.md` | CV review draft render input | Markdown |
| 12 | `nodes/review_cv/.../state.json` | Reviewed CV state | JSON |
| 13 | `nodes/draft_email/.../state.json` | Email draft state | JSON |
| 14 | `nodes/draft_email/.../application_email.md` | Email draft | Markdown |
| 15 | `nodes/review_email/.../state.json` | Reviewed email state | JSON |
| 16 | `nodes/<node>/meta/provenance.json` | Provenance trace | JSON |
| 17 | `nodes/<node>/review/decision.md` + `.json` | Review decisions | MD + JSON |

Supplemental artifacts (outside the 17 primary types):

- `feedback/...` for feedback memory and conflict tracking.
- `final/...` for final deliverables and manifest.
