# Step 6-13 Proposal: Delta-First Generation and Text Reviewers

Status: proposed (pending explicit approval)

Owner scope: planning for next implementation tranche after Step 5 hardening.

Related references:

- `plan/phd2_stepwise_plan.md`
- `plan/index_checklist.md`
- `docs/graph/nodes_summary.md`
- `docs/reference/review_contract_case_decision_and_assistance.md`
- `docs/business_rules/sync_json_md.md`

## 1) Why this proposal exists

This proposal answers three practical findings from current work:

1. Too much text is regenerated from scratch in each LLM node.
2. Large portions of output are deterministic and should not consume LLM budget.
3. CV/letter coherence is better when both are produced from the same semantic pass.

Primary goal:

- reduce token cost and rework while preserving strict HITL review safety.

Non-negotiable rule kept:

- deterministic review nodes remain the only routing authority (`approve`, `request_regeneration`, `reject`).

## 1.1 Confirmed product decisions (locked)

The following decisions are explicitly confirmed and should be treated as implementation constraints:

1. `generate_documents` will be a graph-visible node.
2. `DocumentDeltas` linking for CV injections will use stable ids (not organization name string matching).
3. anti-fluff checks should surface as a reviewer-facing indicator (not hard-fail by default).
4. text-review assistance must be deterministic-only and must not change routing authority.

## 2) Decision summary

Recommended architecture for Step 6-13:

1. Keep current graph contract and review gates (no safety downgrade).
2. Introduce a shared LLM "delta" generation kernel that outputs only variable content.
3. Move stable document scaffolding to deterministic assemblers.
4. Add deterministic text-review indicators as assistance only (never routing authority).

This gives cost reduction without removing control points.

## 3) Node strategy (compatible with current plan)

To avoid breaking the canonical topology immediately, use a hybrid rollout:

### 3.1 Shared generation kernel (new graph-visible node)

- Add `src/nodes/generate_documents/` as a graph-visible LLM producer of `DocumentDeltas`.
- Input is compact and approved-only (no raw uncontrolled context).
- Output is consumed by existing downstream nodes.

### 3.2 Existing generator node names remain in graph

- `generate_motivation_letter` reads letter deltas and assembles deterministic markdown.
- `tailor_cv` reads CV deltas and applies deterministic injections into render-ready markdown.
- `draft_email` reads email delta and assembles deterministic final email draft.

Result:

- graph shape remains recognizable,
- review gates remain unchanged,
- LLM calls can be reduced to one shared call per regeneration cycle.

## 3.3 Deterministic Jinja rendering templates (confirmed)

Generation policy for final text artifacts:

1. `generate_documents` outputs only deltas.
2. deterministic template rendering composes final text.

Template files to add:

- `src/nodes/generate_documents/templates/cv_template.jinja2`
- `src/nodes/generate_documents/templates/cover_letter_template.jinja2`
- `src/nodes/generate_documents/templates/email_template.jinja2`

Template compatibility rule:

- CV dynamic injections must use id-based mapping (`injection.experience_id == job.id`).
- If profile experience entries do not yet have stable ids, introduce deterministic ids during preprocessing and persist them for repeatability.

## 3.4 Confirmed template baseline (from current CV/letter/email format)

The deterministic templates should preserve the current visual/textual structure:

1. CV headings remain uppercase (`SUMMARY`, `EXPERIENCE`, `EDUCATION`, `PUBLICATIONS`, `LANGUAGES`, `SKILLS`).
2. Experience sections keep static bullets and append dynamic delta bullets below them.
3. Cover letter keeps fixed sender header and skeleton while body paragraphs come from deltas.
4. Email reuses motivation subject and deterministic closing block.

Operational note:

- receiver placeholders (name/department/institution) are injected at render time from job metadata, not guessed by the LLM.

## 4) Data contracts (proposed)

## 4.1 `generate_documents` output contract

Use structured output close to the current proposal, with one key stability adjustment:

- replace free-text `company_name` linking with stable `experience_id`.

Proposed contract direction:

- `DocumentDeltas`
  - `cv_summary` (max 3 lines)
  - `cv_injections[]`
    - `experience_id` (must match base profile experience id)
    - `new_bullets[]` (factual English bullets)
  - `letter_deltas`
    - `subject_line`
    - `intro_paragraph`
    - `core_argument_paragraph`
    - `alignment_paragraph`
    - `closing_paragraph`
  - `email_body` (max 2 lines)

Validation additions recommended:

- hard max lengths for summary/email,
- minimum 1 bullet when regeneration asks for CV patch,
- strict id validation against profile snapshot.

Optional helpful field:

- `style_flags` (list) for advisory warnings such as `anti_fluff_term_detected`, `tone_overclaim_risk`.

## 4.2 Inputs to `generate_documents`

Do not read from mutable raw fields. Use approved artifacts only:

1. `nodes/review_match/approved/state.json` or equivalent approved decision payload.
2. `nodes/build_application_context/approved/state.json` (once Step 7 is active).
3. profile base snapshot (`data/reference_data/profile/base_profile/profile_base_data.json`).
4. active review feedback (only from deterministic `decision.json` outputs).

Important correction:

- do not rely on `matched_data.decisions`; use validated decision envelopes from review artifacts.

## 5) Deterministic assembly split

LLM should only generate deltas. Deterministic code should build final documents:

1. fixed CV headers, personal/contact sections, section ordering,
2. fixed motivation letter skeleton (format, salutation frame, section boundaries),
3. fixed email wrapper (subject prefix rules, greeting/closing policy).

This keeps layout stable, reduces hallucination area, and makes review diffs smaller.

## 6) Cost control plan

## 6.1 Hash-based reuse

Create a deterministic input hash for the shared generation kernel from:

- approved match/context refs,
- profile snapshot hash,
- current review feedback hash.

If hash is unchanged, reuse prior `DocumentDeltas` artifact.

## 6.2 Regeneration granularity

On `request_regeneration`:

- if reviewer requests only CV changes, regenerate only CV-relevant deltas,
- preserve unchanged letter/email deltas,
- keep per-part provenance to show what changed and why.

## 6.3 Prompt size minimization

- send filtered profile fields only (experience/education/skills needed for the target deltas),
- send approved claims and explicit patch directives, not full historical payloads.

## 7) Deterministic text-review indicators (critical)

This section is the mandatory addition requested for the next stage.

## 7.1 What "text-reviewer-assist" means (plain language)

`text-reviewer-assist` is a deterministic helper stage that flags quality/policy signals before human review.

Think of it as a strict internal reviewer that says:

- "this paragraph has no approved claim reference,"
- "this sentence contains anti-fluff forbidden terms,"
- "this section violates deterministic style constraints (length/format)."

It does **not** approve or reject anything.

## 7.2 Purpose

Text-review indicators provide deterministic critique before human review to improve first-pass quality.

They are advisory only.

They must never approve/reject routing.

## 7.3 Where they run in graph

For each generated text artifact:

1. generator writes `proposed/state.json` + markdown,
2. `reviewer_<doc>_assist` (deterministic) runs and emits indicator artifacts,
3. deterministic `review_<doc>` remains the gating node.

Examples:

- `generate_motivation_letter -> reviewer_motivation_assist -> review_motivation_letter`
- `tailor_cv -> reviewer_cv_assist -> review_cv`
- `draft_email -> reviewer_email_assist -> review_email`

## 7.4 Contracts for deterministic indicators

Add a shared deterministic indicator envelope:

- `TextReviewIndicator`
  - `severity`: `critical|major|minor`
  - `category`: `grounding|policy|tone|format|consistency`
  - `rule_id`: deterministic rule identifier (for example `ANTI_FLUFF_001`)
  - `target_ref`: paragraph id / bullet id / section id
  - `message`: concise finding
  - `evidence_refs[]`: ids/claims involved when applicable
- `TextReviewAssistEnvelope`
  - `node`
  - `job_id`
  - `source_state_hash`
  - `indicators[]`
  - `summary`

Hard boundary:

- no decision field in assist envelope,
- no routing output from assist nodes.

Mandatory deterministic rule packs for MVP:

1. anti-fluff lexicon match (word-boundary regex),
2. max length checks (summary/email/paragraph bounds),
3. required-structure checks (all required delta fields present),
4. approved-reference coverage checks (when claim refs are expected).

## 7.5 Reviewer artifacts

Persist under each node:

- `nodes/<node>/assist/proposed/state.json`
- `nodes/<node>/assist/proposed/view.md`

Link assist report from review surfaces for operator convenience, but keep `review/decision.md` as the only editable gate input.

## 7.6 How assist output is consumed

- shown to human reviewer as optional guidance,
- optionally transformed into structured patch hints for regeneration prompts,
- never auto-applied to approved artifacts without human decision.

## 7.7 Anti-fluff indicator behavior (confirmed)

Anti-fluff is reviewer-facing in first rollout:

1. deterministic validator scans generated deltas,
2. matched terms are stored as indicator artifacts,
3. review markdown surfaces a "Style Warnings" block.

No routing change in MVP:

- indicators do not auto-fail the step,
- final decision remains with deterministic review gate + human reviewer.

## 8) Tone and policy enforcement

Use dual layer enforcement:

1. Prompt constraints (anti-fluff, factual style, approved-claims-only).
2. Deterministic post-checks:
   - forbidden lexicon checks with word-boundary regex,
   - approved-claim reference checks,
   - max length checks for summary/email.

For MVP:

- violations can be warnings plus reviewer flags.

For hardening phase:

- escalate critical policy violations to fail-closed error.

## 9) Implementation phases (detailed)

## Phase A - foundation (Step 6-7)

1. finalize `build_application_context` approved artifact schema with stable claim refs,
2. harden `review_application_context` stale-hash + ambiguity tests,
3. expose compact context payload for downstream generation.

Acceptance:

- deterministic tests green,
- HITL approve/regenerate/reject run completed on real job.

## Phase B - shared deltas generator

1. add `src/nodes/generate_documents/contract.py`, `logic.py`, prompts,
2. implement delta-only structured output with strict pydantic validation,
3. add hash-based cache/reuse behavior,
4. write artifacts and provenance for generated deltas.

Acceptance:

- schema tests,
- fail-closed tests on invalid ids/oversized fields,
- at least one real-job run.

## Phase C - deterministic assemblers

1. refactor letter/CV/email nodes to assemble from deltas,
2. keep current output artifact contracts for render compatibility,
3. add deterministic formatting tests and snapshot checks.

Acceptance:

- no contract drift in downstream render/package inputs,
- all related tests green.

## Phase D - deterministic text-review indicators

1. add `reviewer_motivation_assist`, `reviewer_cv_assist`, `reviewer_email_assist` nodes,
2. implement deterministic rule packs (anti-fluff, structure, length, grounding references),
3. persist assist artifacts and link them in operator workflow docs,
4. ensure deterministic review nodes remain the sole routing gates,
5. optionally feed indicator findings as bounded guidance in regeneration prompts.

Acceptance:

- explicit tests proving assist nodes cannot route,
- deterministic unit tests for each rule pack,
- HITL run confirms operator can use indicator reports without breaking review parser flow.

## 10) Risks and mitigations

Risk: hidden topology drift from the canonical graph docs.

- Mitigation: first implement as internal shared service; only update canonical graph docs after explicit approval.

Risk: reviewer indicators start acting like implicit gate.

- Mitigation: no decision fields, no route outputs, test guardrails for non-authority.

Risk: stale or inconsistent cross-document deltas.

- Mitigation: source hash in assist and delta artifacts, plus deterministic ref checks during assembly.

## 11) What should be approved before coding

1. policy mode for anti-fluff checks (`warning` vs `fail-closed`) for non-MVP hardening,
2. whether deterministic assist nodes ship immediately with Phase B/C or are introduced in Phase D,
3. final severity thresholds for indicator categories (`critical|major|minor`).
