# Taxonomy Case: Redacting Contracts (Traceable Dual Output)

Related references:

- `docs/reference/contract_composition_framework.md`
- `plan/runtime/templates/llm/00_general_llm_call_template.md`
- `docs/reference/matching_contract_case_matrix_and_escape_hatch.md`
- `plan/runtime/claim_admissibility_and_policy.md`

## Purpose

This document specifies a concrete redacting-case contract where the LLM returns both:

1. machine-traceable JSON state,
2. human-reviewable Markdown draft.

The goal is to preserve narrative quality while keeping deterministic traceability checks in the Data Plane.

## 1) Domain and style primitives

Redacting needs explicit control of both content strategy (what to write) and style policy (how to write).

```python
from pydantic import BaseModel, Field
from typing import Literal


class StyleProfile(BaseModel):
    verbosity_level: Literal["bullet_points", "concise_paragraphs", "detailed_narrative"]
    tone_markers: list[str] = Field(..., description="For example: ['academic', 'formal', 'objective']")
    allowed_formatting: list[str] = Field(..., description="For example: ['bold', 'lists']; empty for plain text")
    forbidden_phrases: list[str] = Field(default_factory=list, description="Cliches and banned phrasing")


class PositioningStrategy(BaseModel):
    target_role_type: str
    primary_narrative: str
    accepted_gaps_handling: list[str] = Field(
        ...,
        description="How to safely justify missing requirements"
    )
```

## 2) Input contract (`RedactingInput`)

The redacting node receives approved analytical context, style controls, and optional reusable feedback memory.

```python
from pydantic import BaseModel, Field


class RedactingInput(BaseModel):
    job_id: str

    # what to write
    approved_mappings: list[RequirementMapping]
    strategy: PositioningStrategy

    # how to write
    style_profile: StyleProfile

    # reusable writing rules from previous runs
    active_feedback: list[FeedbackRule] = Field(default_factory=list)
```

## 3) Output contract (`RedactEnvelope`)

Redacting outputs are dual by design:

- structured JSON state for machine checks,
- markdown content for human review.

```python
from pydantic import BaseModel, Field


class RedactingState(BaseModel):
    """Canonical machine state used for traceability checks."""

    schema_version: str = "1.0"
    doc_type: str = Field(..., description="For example motivation_letter, cv_draft, application_email")

    consumed_req_ids: list[str]
    consumed_evidence_ids: list[str]

    markdown_ref: str


class RedactEnvelope(BaseModel):
    """Complete LLM output contract for redacting nodes."""

    state: RedactingState
    markdown_content: str = Field(..., description="Final draft in pure Markdown")
    suggested_filename: str = Field(..., description="For example letter.md or to_render.md")
```

Design rule:

- `node.py` must persist JSON state and markdown draft separately using Data Plane writers.

## 4) `logic.py` integration

Use the Jinja rendering contract and request a structured `RedactEnvelope`.

```python
from pathlib import Path


def run_logic(
    logic_input: RedactingInput,
    runtime: LLMRuntime,
    prompt_bundle: PromptBundle,
) -> RedactEnvelope:
    user_prompt = render_user_template(
        prompt_dir=Path("prompt"),
        template_name="user_template.md",
        payload=logic_input.model_dump(),
    )

    return runtime.generate_structured(
        system_prompt=prompt_bundle.system_prompt,
        user_prompt=user_prompt,
        output_schema=RedactEnvelope,
    )
```

## 5) Deterministic anti-hallucination check

`RedactingState` enables a deterministic guard before human review:

1. every cited id in `consumed_evidence_ids` must exist in approved upstream mapping,
2. every `consumed_req_id` must exist in approved requirement mapping,
3. unknown ids fail closed,
4. optional strict mode can check that salient markdown claims map to listed consumed ids.

This blocks promotional hallucination paths early.

## 6) Base-state inheritance pattern

Use a shared base for common traceability fields and specialize per document type.

```python
from typing import Literal


class RedactingStateBase(BaseModel):
    schema_version: str = "1.0"
    consumed_req_ids: list[str]
    consumed_evidence_ids: list[str]


class EmailState(RedactingStateBase):
    doc_type: Literal["application_email"] = "application_email"
    subject: str
    salutation: str
    body: str


class MotivationLetterState(RedactingStateBase):
    doc_type: Literal["motivation_letter"] = "motivation_letter"
    section_rationale: dict[str, str]


class CVTailoringState(RedactingStateBase):
    doc_type: Literal["cv_tailoring_notes"] = "cv_tailoring_notes"
    emphasized_areas: list[str]
    omitted_areas: list[str]
```

Recommended envelope typing:

- use discriminated unions for `state` where multiple redacting state variants are expected.

## 7) Why this contract is strong

1. Narrative flexibility without losing machine governance.
2. Traceability-first by design (`consumed_*` ids).
3. Deterministic quality gates can run before human review.
4. Reusable base state keeps schema evolution consistent across letter/CV/email nodes.
