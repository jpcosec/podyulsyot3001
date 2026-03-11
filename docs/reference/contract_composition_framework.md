# Contract Composition Framework: Envelopes and Primitives

Related references:

- `docs/philosophy/execution_taxonomy_abstract.md`
- `docs/templates/node_template_discipline.md`
- `docs/reference/artifact_schemas.md`
- `docs/reference/extracting_contract_case_job_understanding.md`
- `docs/reference/matching_contract_case_matrix_and_escape_hatch.md`
- `docs/reference/redacting_contract_case_traceable_dual_output.md`

## Purpose

This document defines the composition-first strategy for `contract.py` schemas across all PhD 2.0 nodes.

To avoid monolithic and rigid schemas, contracts are built by combining reusable blocks across three dimensions:

1. taxonomy envelope (root shape),
2. domain primitives (business entities),
3. style primitives (text density and formatting constraints).

## Authority scope

- Canonical owner for contract composition rules in `contract.py`.
- Not the owner of taxonomy definitions (owned by `docs/philosophy/execution_taxonomy_abstract.md`).
- Not the owner of artifact storage paths (owned by `docs/reference/artifact_schemas.md`).

## 1) Taxonomy envelopes

Envelopes define the root `BaseModel` shape for node output and, when useful, for node input wrappers.
Envelope choice is dictated by taxonomy leaf.

### `ExtractEnvelope`

Use for extracting/consolidating structured facts.

Typical shape:

- list of extracted entities,
- extraction summary/metadata.

### `MatchEnvelope`

Use for analytical requirement-to-evidence mapping.

Typical shape:

- list of `RequirementMapping`,
- source-text pointer for review UX (`source_text_ref`),
- proposed claims and unmapped evidence summary.

### `RedactEnvelope`

Use for human-facing narrative generation nodes.

Typical shape:

- polymorphic JSON state with consumed dependency trace,
- markdown draft content as plain string,
- deterministic metadata for Data Plane persistence.

### `ReviewEnvelope`

Use for review outcomes and distilled learning.

Typical shape:

- review decisions,
- reviewer notes,
- extracted reusable feedback rules.

Note:

- review gate authority still belongs to deterministic review parser nodes; this envelope does not change that rule.

## 2) Domain primitives

Primitives are reusable business entities used inside envelopes.

### `JobRequirement`

Canonical requirement unit from job understanding:

- `req_id`, `text`, `priority`.

### `ProfileEvidence`

Atomic profile fact:

- `evidence_id`, `evidence_type`, `description`, `source_ref`.

### `EvidenceEvaluation`

Matrix-cell primitive for one requirement/evidence intersection.

Minimum expectation:

- target evidence id,
- normalized match score (`0.0..1.0`),
- reason for match,
- reason against match.

### `RequirementMapping`

Matrix-row primitive for one requirement and all evaluated evidence.

Minimum expectation:

- requirement id and readable requirement text,
- coverage status (`full|partial|none`),
- list of `EvidenceEvaluation`,
- optional risk flags.

### `ReviewDirective`

Tagged directive extracted from reviewer notes.

Minimum expectation:

- scope (`local|global`),
- directive type, target, action,
- normalized reusable rule,
- confidence (`0.0..1.0`).

### `ParsedDecision`

Deterministic decision unit for one reviewed block.

Minimum expectation:

- block id,
- final decision (`approve|request_regeneration|reject`),
- optional notes,
- parsed directive tags.

### `FeedbackRule`

Distilled reusable rule for future runs:

- normalized rule text,
- scope, category, confidence, provenance ref.

## 3) Style and verbosity primitives

Narrative nodes need explicit writing constraints as typed inputs.

### `StyleProfile`

`StyleProfile` is injected in generative node input to constrain tone and formatting.

Fields:

- `verbosity_level`: `bullet_points|concise_paragraphs|detailed_narrative`
- `tone_markers`: list like `academic`, `formal`, `objective`
- `allowed_formatting`: markdown feature controls (for example forbid tables or bold)
- `forbidden_phrases`: cliches and banned phrasing

Design rule:

- style constraints are contract fields, not hidden prompt-only instructions.

## 4) Polymorphism and inheritance (`RedactEnvelope` case)

All redacting nodes return a `RedactEnvelope`, but each document type needs different internal state fields.

Use inheritance with a shared traceability base:

```python
from pydantic import BaseModel
from typing import Literal


class RedactingStateBase(BaseModel):
    schema_version: str = "1.0"
    consumed_req_ids: list[str]
    consumed_evidence_ids: list[str]


class EmailState(RedactingStateBase):
    doc_type: Literal["application_email"] = "application_email"
    subject: str
    salutation: str


class MotivationLetterState(RedactingStateBase):
    doc_type: Literal["motivation_letter"] = "motivation_letter"
    section_rationale: dict[str, str]


class CVTailoringState(RedactingStateBase):
    doc_type: Literal["cv_tailoring_notes"] = "cv_tailoring_notes"
    emphasized_areas: list[str]
    omitted_areas: list[str]
```

Envelope rule:

- `RedactEnvelope.state` accepts any subtype of `RedactingStateBase` (prefer discriminated unions).

## 5) Validation invariants

All primitives and envelopes should follow these invariants:

1. stable identifiers (`req_id`, `evidence_id`, `claim_id`) are required,
2. enums are closed where possible (priority, decision, coverage),
3. cross-ref integrity must be checkable (`RequirementMapping.req_id` exists upstream),
4. contracts should avoid optional ambiguity for gating fields,
5. `schema_version` and `doc_type` are explicit for envelope outputs.

## Benefits

1. Consistency: new nodes follow one predictable contract strategy.
2. Reuse: the same primitives flow across multiple stages.
3. Auditability: traceability fields and explicit style constraints reduce wax-model behavior.
4. Maintainability: schema evolution is local to primitives/envelopes, not copied per node.

## Worked cases

- Extracting case (`extract_understand`): `docs/reference/extracting_contract_case_job_understanding.md`
- Matching case (`match`): `docs/reference/matching_contract_case_matrix_and_escape_hatch.md`
- Redacting case (`generate_motivation_letter`/`tailor_cv`/`draft_email`): `docs/reference/redacting_contract_case_traceable_dual_output.md`
- Reviewing case (`review_*` and `feedback_distill`): `docs/reference/review_contract_case_decision_and_assistance.md`
