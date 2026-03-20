Document Schemas and Structures for the Application Pipeline
===========================================================

Goal
----

Define a stable schema/structure for the main pipeline documents so that each artifact has:
- a clear purpose
- a clear owner stage
- a stable front matter / JSON contract
- a clear distinction between:
  - machine-readable state
  - human review surface
  - render-ready content

This proposal is based on the observed structure in:
- profile_base_data.json
- 01_matcher.json
- match_proposal.md
- match_proposal.round1.md
- motivation_letter.pre.md
- cv.to_render.md

Observed patterns from the examples
-----------------------------------

1. profile_base_data.json already behaves like a canonical profile knowledge base.
2. 01_matcher.json already behaves like structured semantic state:
   - job
   - evidence_items
   - mapping
   - render hints
3. match_proposal.md already behaves like a review interface with:
   - YAML front matter
   - requirement-by-requirement editable blocks
4. match_proposal.round1.md shows iterative review and reviewer notes.
5. motivation_letter.pre.md already shows a "pre-review draft" concept.
6. cv.to_render.md already shows a render-facing artifact.

This suggests a clean split:
- JSON files = semantic state / contracts
- Markdown files = reviewable or renderable documents

--------------------------------------------------
1. profile_base_data.json
--------------------------------------------------

Purpose
- Canonical profile knowledge base.
- Long-lived source of truth for personal/professional data.

Type
- JSON

Owner stage
- profile ingestion / profile management

Recommended top-level schema
----------------------------

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
        {
          "label": "current",
          "value": "..."
        }
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

Recommendations
---------------
- Keep this document factual only.
- Do not store application-specific positioning here.
- Do not inject temporary narrative edits into this file.

--------------------------------------------------
2. planning/job_understanding.json
--------------------------------------------------

Purpose
- Structured interpretation of the job posting.
- Derived from ingest + extraction.
- Serves as stable job-side semantic state.

Type
- JSON

Owner stage
- extract_understand

Recommended schema
------------------

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
  "raw_text_ref": "job.md"
}
```

Recommendations
---------------
- Keep this job-only.
- Avoid mixing profile-side interpretation here.

--------------------------------------------------
3. cv/pipeline_intermediates/01_matcher.json
--------------------------------------------------

Purpose
- Machine-readable requirement-to-evidence mapping state.

Type
- JSON

Owner stage
- match

Observed strong pattern
-----------------------
The current file already includes:
- job
- evidence_items
- mapping
- render hints

Recommended schema
------------------

```json
{
  "schema_version": "1.0",
  "job_id": "201397",
  "generated_at": "2026-03-03T13:44:11Z",
  "inputs": {
    "job_understanding_ref": "planning/job_understanding.json",
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
      "type": "cv_line",
      "text": "...",
      "source_ref": "profile.experience[0].achievements[0]"
    }
  ],
  "mapping": [
    {
      "req_id": "R1",
      "priority": "must",
      "coverage": "partial",
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
      "confidence": "moderate",
      "claim_type": "bridging"
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
    "ordering": ["summary", "experience", "education", "publications", "skills", "languages"],
    "style_rules": {}
  }
}
```

Recommendations
---------------
- This should remain owned by the matcher.
- Later stages should reference it, not overwrite it.

--------------------------------------------------
4. planning/match_proposal.md
--------------------------------------------------

Purpose
- Human review surface for matching.
- Editable requirement-by-requirement proposal.

Type
- Markdown with YAML front matter

Owner stage
- match

Observed pattern
----------------
Your current file already uses:
- YAML front matter
- heading
- requirement sections
- Decision / Edited Claim / Notes

Recommended structure
---------------------

```markdown
---
schema_version: "1.0"
doc_type: "match_proposal"
status: "proposed"
job_id: "201397"
generated_at: "2026-03-03T13:44:11Z"
source_matcher_ref: "cv/pipeline_intermediates/01_matcher.json"
profile_ref: "profile/profile_base_data.json"
job_ref: "planning/job_understanding.json"
review_round: 0
---

# Match Proposal: <job title>

## Review Instructions
- Approve when the claim is accurate and strategically good.
- Edit when the claim needs refinement.
- Reject when the claim should not be used.
- Use Notes for reviewer rationale.

## Requirements Mapping

### R1: <requirement text> [PARTIAL]
Evidence IDs: P_EDU_04, P_EXP_01
Evidence: ...
Claim: ...
Confidence: moderate
Decision: [ ] approve  [ ] edit  [ ] reject
Edited Claim:
Notes:

### R2: <requirement text> [FULL]
...
```

Recommended optional sections
-----------------------------
- ## Gaps (no evidence found)
- ## Strategic Notes
- ## Proposed Summary

Recommendations
---------------
- Keep it intentionally editable.
- Do not treat it as validated truth.

--------------------------------------------------
5. planning/reviewed_mapping.json
--------------------------------------------------

Purpose
- Validated post-review matching state.
- Main downstream source of truth after human review.

Type
- JSON

Owner stage
- review_match

Recommended schema
------------------

```json
{
  "schema_version": "1.0",
  "doc_type": "reviewed_mapping",
  "job_id": "201397",
  "reviewed_at": "2026-03-03T15:00:00Z",
  "source_match_proposal_ref": "planning/match_proposal.round1.md",
  "source_matcher_ref": "cv/pipeline_intermediates/01_matcher.json",
  "decisions": [
    {
      "req_id": "R1",
      "requirement_text": "...",
      "initial_coverage": "partial",
      "final_decision": "edit",
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
      "status": "accepted_gap",
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

Recommendations
---------------
- This is the first validated semantic state for downstream generators.

--------------------------------------------------
6. planning/application_context.json
--------------------------------------------------

Purpose
- Shared grounded context for letter, CV, and email generation.

Type
- JSON

Owner stage
- build_application_context

Recommended schema
------------------

```json
{
  "schema_version": "1.0",
  "doc_type": "application_context",
  "job_id": "201397",
  "generated_at": "2026-03-03T15:10:00Z",
  "sources": {
    "reviewed_mapping_ref": "planning/reviewed_mapping.json",
    "profile_ref": "profile/profile_base_data.json",
    "job_ref": "planning/job_understanding.json"
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
  "approved_strengths": [],
  "bridging_claims": [],
  "accepted_gaps": [],
  "target_emphasis": {
    "letter": [],
    "cv": [],
    "email": []
  },
  "evidence_priority_order": []
}
```

Recommendations
---------------
- This should be the main input for all downstream generation.

--------------------------------------------------
7. planning/motivation_letter.pre.md
--------------------------------------------------

Purpose
- First reviewable letter draft.

Type
- Markdown with YAML front matter

Owner stage
- generate_motivation_letter

Observed pattern
----------------
The current file is a plain letter draft.
It would benefit from explicit metadata.

Recommended structure
---------------------

```markdown
---
schema_version: "1.0"
doc_type: "motivation_letter_draft"
status: "pre_review"
job_id: "201397"
generated_at: "2026-03-03T15:20:00Z"
application_context_ref: "planning/application_context.json"
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

Recommendations
---------------
- Keep it human-readable and editable.
- Do not hide key constraints only inside prose; keep them traceable in JSON too.

--------------------------------------------------
8. planning/motivation_letter.reviewed.json
--------------------------------------------------

Purpose
- Structured reviewed state of the motivation letter.

Type
- JSON

Owner stage
- review_motivation_letter

Recommended schema
------------------

```json
{
  "schema_version": "1.0",
  "doc_type": "motivation_letter_reviewed",
  "job_id": "201397",
  "reviewed_at": "2026-03-03T16:00:00Z",
  "source_draft_ref": "planning/motivation_letter.pre.md",
  "final_markdown_ref": "planning/motivation_letter.md",
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

--------------------------------------------------
9. planning/motivation_letter.md
--------------------------------------------------

Purpose
- Approved final letter content.

Type
- Markdown

Owner stage
- review_motivation_letter

Recommended structure
---------------------
Same body shape as the draft, but status = reviewed/final in front matter.

```markdown
---
schema_version: "1.0"
doc_type: "motivation_letter"
status: "reviewed"
job_id: "201397"
reviewed_at: "2026-03-03T16:00:00Z"
application_context_ref: "planning/application_context.json"
reviewed_json_ref: "planning/motivation_letter.reviewed.json"
language: "en"
---
```

--------------------------------------------------
10. planning/cv_tailoring.md
--------------------------------------------------

Purpose
- Human-readable explanation of CV adaptation decisions.

Type
- Markdown

Owner stage
- tailor_cv

Recommended structure
---------------------

```markdown
---
schema_version: "1.0"
doc_type: "cv_tailoring_notes"
status: "generated"
job_id: "201397"
generated_at: "2026-03-03T16:10:00Z"
application_context_ref: "planning/application_context.json"
motivation_review_ref: "planning/motivation_letter.reviewed.json"
---

# CV Tailoring Notes

## Target Emphasis
- ...
- ...

## De-emphasized Areas
- ...
- ...

## Ordering Decisions
- Summary first because ...
- Publications moved above skills because ...

## Risk Controls
- Avoid implying ...
- Phrase X as ...
```

--------------------------------------------------
11. cv/to_render.md
--------------------------------------------------

Purpose
- Renderer-facing CV content.
- Final semantic content before layout/rendering.

Type
- Markdown with lightweight structure

Owner stage
- tailor_cv

Observed pattern
----------------
Your current artifact already suggests a dedicated renderer input.

Recommended structure
---------------------

```markdown
---
schema_version: "1.0"
doc_type: "cv_render_input"
status: "final_content"
job_id: "201397"
generated_at: "2026-03-03T16:15:00Z"
application_context_ref: "planning/application_context.json"
tailoring_notes_ref: "planning/cv_tailoring.md"
language: "en"
render_profile: "academic_phd"
---

# Juan Pablo Ruiz Rodriguez

## Header
- Berlin, Germany
- juanpablo.ruiz.r@gmail.com
- +49 ...
- LinkedIn
- GitHub

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

Recommendations
---------------
- Keep it content-only.
- Avoid review checkboxes or editorial comments in this file.

--------------------------------------------------
12. planning/application_email.md
--------------------------------------------------

Purpose
- Final human-readable email draft.

Type
- Markdown with YAML front matter

Owner stage
- draft_email

Recommended structure
---------------------

```markdown
---
schema_version: "1.0"
doc_type: "application_email"
status: "generated"
job_id: "201397"
generated_at: "2026-03-03T16:20:00Z"
application_context_ref: "planning/application_context.json"
motivation_review_ref: "planning/motivation_letter.reviewed.json"
language: "en"
recipient_name: "Prof. Dr. Eva Wiese"
recipient_email: "sekretariat@kke.tu-berlin.de"
subject_line: "Application for Research Assistant (Ref. V-67/26)"
---

Subject: Application for Research Assistant (Ref. V-67/26)

Dear Prof. Dr. Eva Wiese,

Please find attached my application materials for the Research Assistant position (Ref. V-67/26), including my CV and motivation letter.

<1–2 concise paragraphs>

Kind regards,
Juan Pablo Ruiz Rodriguez
```

--------------------------------------------------
13. feedback/events/<stage>/<timestamp>.json
--------------------------------------------------

Purpose
- Structured feedback events for any reviewable stage.

Type
- JSON

Owner stage
- any review stage

Recommended schema
------------------

```json
{
  "schema_version": "1.0",
  "feedback_id": "fb_000001",
  "created_at": "2026-03-03T15:05:00Z",
  "stage": "matching",
  "scope": "global",
  "type": "strategic",
  "job_id": "201397",
  "artifact_ref": "planning/match_proposal.round1.md",
  "target_ref": "R1",
  "reviewer_comment": "Do not oversell direct domain fit; use bridge framing.",
  "normalized_rule": "When domain fit is partial, use bridge language grounded in real projects.",
  "applies_to_current_case": true,
  "reusable": true,
  "confidence": 0.93
}
```

--------------------------------------------------
14. feedback/active_memory.yaml
--------------------------------------------------

Purpose
- Distilled reusable feedback rules for prompt injection.

Type
- YAML

Owner stage
- feedback distillation / memory maintenance

Recommended structure
---------------------

```yaml
matching:
  strategic:
    - rule: "When direct domain fit is partial, prefer bridge framing over equivalence claims."
      tags: [phd, academic, truthfulness]
      confidence: 0.93

motivation_letter:
  stylistic:
    - rule: "Avoid generic enthusiasm statements; tie motivation to a specific research direction."
      tags: [academic, writing]
      confidence: 0.95

cv_tailoring:
  factual:
    - rule: "Do not imply hands-on data collection unless explicitly verified."
      tags: [claims, truthfulness]
      confidence: 0.99
```

--------------------------------------------------
15. output artifacts
--------------------------------------------------

Purpose
- Final rendered deliverables.

Recommended set
---------------

output/cv.pdf
output/motivation_letter.pdf
output/Final_Application.pdf

Optional
--------
output/application_email.txt
output/application_bundle.zip

--------------------------------------------------
Document role summary
--------------------------------------------------

1. Canonical knowledge base
- profile_base_data.json

2. Job-side semantic state
- planning/job_understanding.json

3. Machine-readable matching state
- cv/pipeline_intermediates/01_matcher.json

4. Human review surface
- planning/match_proposal.md

5. Validated reviewed match state
- planning/reviewed_mapping.json

6. Grounded downstream context
- planning/application_context.json

7. Reviewable letter draft
- planning/motivation_letter.pre.md

8. Structured reviewed letter state
- planning/motivation_letter.reviewed.json

9. Final reviewed letter
- planning/motivation_letter.md

10. CV strategy notes
- planning/cv_tailoring.md

11. Renderer input for CV
- cv/to_render.md

12. Final email draft
- planning/application_email.md

13. Structured feedback events
- feedback/events/<stage>/<timestamp>.json

14. Distilled reusable memory
- feedback/active_memory.yaml

--------------------------------------------------
Key design rule
--------------------------------------------------

Use this split consistently:

- JSON = truth / state / machine contract
- Markdown = review surface or render content
- YAML = distilled active rules / config

That single rule will keep the pipeline much cleaner.
