Application Pipeline Contracts — Inputs / Outputs
=================================================

Purpose
-------

This document makes explicit the input/output contracts of the application pipeline,
using the provided example artifacts as reference.

Observed example artifacts
--------------------------

Input / context artifacts observed:
- profile_base_data.json
- 01_matcher.json
- match_proposal.md
- match_proposal.round1.md
- motivation_letter.pre.md
- cv.to_render.md

Key design goal
---------------

The main pipeline should not be understood only as a sequence of files.
It should be understood as a sequence of stage contracts:

stage input -> stage transformation -> stage output -> reviewable artifact -> next stage input

Recommended main stages
-----------------------

1. ingest
2. extract_understand
3. match
4. review_match
5. build_application_context
6. generate_motivation_letter
7. review_motivation_letter
8. tailor_cv
9. draft_email
10. render
11. package

--------------------------------------------------
1. INGEST
--------------------------------------------------

Purpose
- Receive a URL or a regenerate-mode raw source.
- Normalize the job posting into stable internal artifacts.

Inputs
- URL
  or
- raw/raw.html (regenerate mode)

Outputs
- raw/raw.html
- raw/source_text.md
- raw/extracted.json
- job.md

Source of truth
- job.md = canonical job-facing artifact for downstream stages
- raw/extracted.json = structured machine-readable extraction

Notes
- Downstream stages should avoid re-scraping whenever possible.
- Once job.md exists, it should be the standard semantic reference for the posting.

--------------------------------------------------
2. EXTRACT / UNDERSTAND
--------------------------------------------------

Purpose
- Turn scraped posting content into structured requirements, themes, responsibilities,
  and task-relevant metadata.

Inputs
- job.md
- raw/extracted.json

Outputs
- planning/job_understanding.json   (recommended)
- planning/requirements.json        (recommended)
- planning/keywords.json

Observed equivalent evidence
- In the provided matcher artifact, the "job" object already contains:
  - requirements
  - themes
  - responsibilities
  - deadline
  - institution
  - contact data

Recommendation
- Split this into a dedicated extraction-stage artifact instead of embedding everything
  only inside matcher output.

Recommended source of truth
- planning/job_understanding.json

--------------------------------------------------
3. MATCH
--------------------------------------------------

Purpose
- Compare job requirements against the profile knowledge base.
- Produce a structured mapping plus a human-reviewable proposal.

Inputs
- planning/job_understanding.json
- profile/profile_base_data.json
- historical feedback memory relevant to matching

Outputs
- cv/pipeline_intermediates/01_matcher.json
- planning/match_proposal.md
- planning/match_proposal.roundN.md (if regenerated)
- planning/keywords.json 
- delete / invalidate planning/reviewed_mapping.json if stale

Observed example artifacts
- 01_matcher.json
- match_proposal.md
- match_proposal.round1.md

What 01_matcher.json already shows well
- job metadata
- evidence_items
- requirement-to-evidence mapping
- proposed render hints

What match_proposal.md already shows well
- human-readable requirement-by-requirement review sheet
- editable claims
- decision boxes
- notes for reviewer

Recommended contract
- 01_matcher.json = machine-readable matching state
- match_proposal.md = human review surface for matching

Source of truth
- Before review: cv/pipeline_intermediates/01_matcher.json
- After review: planning/reviewed_mapping.json

Important design note
- The markdown proposal is not the final truth.
- It is the editable review interface.
- The reviewed_mapping.json should become the validated source of truth for downstream generation.

--------------------------------------------------
4. REVIEW MATCH
--------------------------------------------------

Purpose
- Let the human approve, reject, or refine requirement-level claims.
- Convert review decisions into validated structured context.

Inputs
- planning/match_proposal.md
- cv/pipeline_intermediates/01_matcher.json
- optional historical feedback suggestions

Outputs
- planning/reviewed_mapping.json
- feedback/events/matching/*.json   (recommended)
- feedback/history.jsonl            (recommended aggregate append-only log)

Observed example value
- match_proposal.round1.md clearly shows review comments that should be persisted
  not only as ad-hoc markdown notes, but as structured feedback.

Recommended source of truth
- planning/reviewed_mapping.json

Recommended minimum structure
- req_id
- final_decision
- approved_claim
- edited_claim
- reviewer_notes
- reusable_feedback_flag
- confidence_after_review

--------------------------------------------------
5. BUILD APPLICATION CONTEXT
--------------------------------------------------

Purpose
- Consolidate the validated match into a reusable, grounded context for all later writing.

Inputs
- planning/reviewed_mapping.json
- planning/job_understanding.json
- profile/profile_base_data.json
- relevant historical feedback memory

Outputs
- planning/application_context.json   (recommended)
- planning/application_strategy.md    (recommended optional human-readable summary)

Why this stage matters
- It prevents each downstream generator from reinterpreting the job independently.
- It becomes the shared source of truth for:
  - motivation letter
  - CV tailoring
  - email drafting

Recommended content
- approved strengths
- explicit gaps and how to phrase them
- positioning strategy
- forbidden claims
- tone hints
- target emphasis areas

Source of truth
- planning/application_context.json

--------------------------------------------------
6. GENERATE MOTIVATION LETTER
--------------------------------------------------

Purpose
- Draft the motivation letter based on validated application context.

Inputs
- planning/application_context.json
- profile/profile_base_data.json
- relevant historical feedback memory for letter writing

Outputs
- planning/motivation_letter.pre.md
- planning/motivation_letter.json

Observed example artifact
- motivation_letter.pre.md

Recommended contract
- motivation_letter.pre.md = first reviewable draft
- motivation_letter.json = structured representation of claims / sections / rationale

Suggested motivation_letter.json contents
- opening
- fit_summary
- research_alignment
- methods_alignment
- truthfulness_constraints
- closing
- referenced_requirements

Source of truth
- Before review: planning/motivation_letter.pre.md + planning/motivation_letter.json
- After review: planning/motivation_letter.md + planning/motivation_letter.reviewed.json (recommended)

--------------------------------------------------
7. REVIEW MOTIVATION LETTER
--------------------------------------------------

Purpose
- Review and improve the letter.
- Extract reusable writing and positioning feedback.

Inputs
- planning/motivation_letter.pre.md
- planning/motivation_letter.json
- planning/application_context.json

Outputs
- planning/motivation_letter.md
- planning/motivation_letter.reviewed.json   (recommended)
- feedback/events/motivation_letter/*.json   (recommended)

Recommended source of truth
- planning/motivation_letter.md
- planning/motivation_letter.reviewed.json

Important design note
- The reviewed motivation letter should influence CV and email.
- That means this stage is not just a document edit.
- It is a strategic alignment update.

--------------------------------------------------
8. TAILOR CV <!--  we are missing review cv step-->
--------------------------------------------------

Purpose
- Produce a CV version aligned with the validated application context and reviewed letter.

Inputs
- planning/application_context.json
- planning/motivation_letter.reviewed.json (or motivation_letter.md)
- profile/profile_base_data.json
- historical feedback memory for CV tailoring

Outputs
- planning/cv_tailoring.md
- cv/to_render.md
- cv/pipeline_intermediates/01_matcher.json   (reuse if needed, but avoid rewriting ownership ambiguously)
- cv/pipeline_intermediates/02_seller.json
- cv/pipeline_intermediates/03_reality_checker.json

Observed example artifact
- cv.to_render.md

Recommended contract
- cv/to_render.md = renderer input
- cv_tailoring.md = reviewer-facing explanation of tailoring decisions

Recommended source of truth
- cv/to_render.md

Important design note
- If 01_matcher.json is rewritten here, ownership gets blurry.
- Better:
  - 01_matcher.json stays owned by matching
  - downstream stages can reference it, but should write their own artifacts

--------------------------------------------------
9. DRAFT EMAIL
--------------------------------------------------

Purpose
- Draft the application email consistent with the validated positioning.

Inputs
- planning/application_context.json
- planning/motivation_letter.reviewed.json
- optional job metadata (contact, reference number)

Outputs
- planning/application_email.md
- planning/application_email.json   (recommended)

Recommended source of truth
- planning/application_email.md

--------------------------------------------------
10. RENDER
--------------------------------------------------

Purpose
- Convert final content artifacts into renderable deliverables.

Inputs
- cv/to_render.md
- planning/motivation_letter.md
- planning/application_email.md (optional if renderable)
- job metadata
- profile metadata
- render config / templates

Outputs
- output/cv.pdf
- output/motivation_letter.pdf
- optional output/application_email.txt or .pdf
- cv/ats/... template artifacts if ATS rendering mode is enabled

Source of truth
- output/cv.pdf
- output/motivation_letter.pdf

Important design note
- Render should not change content logic.
- It should only materialize already-approved content.

--------------------------------------------------
11. PACKAGE
--------------------------------------------------

Purpose
- Combine final artifacts into final submission package.

Inputs
- output/cv.pdf
- output/motivation_letter.pdf
- optional supporting docs

Outputs
- output/Final_Application.pdf
- output/application_bundle.zip   (recommended if multiple files are needed)

Source of truth
- output/Final_Application.pdf
  or
- output/application_bundle.zip

--------------------------------------------------
CROSS-CUTTING: HISTORICAL FEEDBACK
--------------------------------------------------

Design principle
- Every reviewable stage should produce reusable feedback when appropriate.

Stages that should write feedback
- extract_understand
- match
- application_context
- motivation_letter
- cv_tailoring
- email
- render

Recommended storage
- feedback/history.jsonl                # append-only log
- feedback/active_memory.yaml           # distilled reusable rules
- feedback/events/<stage>/<timestamp>.json

Recommended feedback event fields
- feedback_id
- stage
- scope: local | global
- type: factual | strategic | stylistic | structural | process
- source_job_id
- artifact_ref
- original_text
- reviewer_comment
- normalized_rule
- applies_to_current_case
- reusable
- confidence
- created_at

--------------------------------------------------
RUNTIME / CHECKPOINT STATE
--------------------------------------------------

Purpose
- Persist execution state and allow resume / graph-status.

Observed path
- data/pipelined_data/<source>/<job_id>/.graph/checkpoints.db

Recommendation
- Treat checkpoint DB as runtime state, not semantic content.
- Do not use it as a substitute for validated artifacts.

--------------------------------------------------
MINIMUM CLEAN CONTRACT SET
--------------------------------------------------

If you want the cleanest version of the system, the minimum important files would be:

1. job.md
2. planning/job_understanding.json
3. profile/profile_base_data.json
4. cv/pipeline_intermediates/01_matcher.json
5. planning/match_proposal.md
6. planning/reviewed_mapping.json
7. planning/application_context.json
8. planning/motivation_letter.pre.md
9. planning/motivation_letter.md
10. cv/to_render.md
11. planning/application_email.md
12. output/cv.pdf
13. output/motivation_letter.pdf
14. output/Final_Application.pdf
15. feedback/history.jsonl
16. feedback/active_memory.yaml

--------------------------------------------------
RECOMMENDED SIMPLE FLOW
--------------------------------------------------

URL
-> ingest
-> job.md
-> job_understanding.json
-> match
-> 01_matcher.json + match_proposal.md
-> human review
-> reviewed_mapping.json
-> application_context.json
-> motivation_letter.pre.md
-> motivation review
-> motivation_letter.md
-> cv/to_render.md + application_email.md
-> render
-> final outputs

--------------------------------------------------
FILES PROVIDED AS EXAMPLES
--------------------------------------------------

The uploaded examples support this contract design:

- 01_matcher.json
  shows a machine-readable match state with requirements, evidence items, mapping,
  and render hints.

- match_proposal.md
  shows a human-readable requirement review sheet.

- match_proposal.round1.md
  shows review iteration and valuable reviewer notes that should be persisted in structured form.

- motivation_letter.pre.md
  shows that the letter already has a pre-review stage.

- cv.to_render.md
  shows a dedicated renderer-facing CV artifact.

- profile_base_data.json
  shows a strong candidate for the canonical profile knowledge base.

Final takeaway
--------------

The most important architectural clarification is:

- markdown proposal files are review surfaces
- reviewed json files should be validated semantic state
- render inputs should be separate from review artifacts
- historical feedback should exist for every reviewable stage
