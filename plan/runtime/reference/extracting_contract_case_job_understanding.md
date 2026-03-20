# Taxonomy Case: Extracting Contracts (Job Understanding)

Related references:

- `docs/reference/contract_composition_framework.md`
- `plan/archive/execution_taxonomy_abstract.md`
- `plan/runtime/node_template_discipline.md`
- `plan/runtime/templates/llm/00_general_llm_call_template.md`

## Purpose

This document provides a concrete extracting-case specification using the envelope + primitive composition framework.

Scope:

- define extracting domain primitives,
- define extracting input and output contracts,
- show `logic.py` integration with structured LLM output,
- capture a future extension for profile extraction harmonization.

## 1) Domain primitives (extracting)

Primitives model isolated business facts. They do not encode pipeline routing.

```python
from pydantic import BaseModel, Field
from typing import Literal


class JobRequirement(BaseModel):
    id: str = Field(..., description="Unique requirement id, for example R1, R2")
    text: str = Field(..., description="Literal or normalized requirement text")
    priority: Literal["must", "nice"] = Field(..., description="Blocking vs desirable")


class JobConstraint(BaseModel):
    constraint_type: Literal["language", "application_mode", "format", "legal", "other"]
    description: str


class JobTheme(BaseModel):
    theme_name: str
    description: str


class ProfileEvidence(BaseModel):
    id: str = Field(..., description="Unique evidence id, for example P_EXP_01, P_EDU_02")
    evidence_type: Literal[
        "role", "project", "publication", "education",
        "skill", "coursework", "summary_line", "other"
    ]
    text: str = Field(..., description="Evidence statement")
```

## 2) Taxonomy envelope (`ExtractEnvelope` implementation)

For `extract_understand`, the concrete output contract is:

```python
from pydantic import BaseModel, Field


class JobUnderstandingExtract(BaseModel):
    """ExtractEnvelope implementation for `extract_understand`."""

    schema_version: str = "1.0"
    doc_type: str = "job_understanding"

    # Job metadata
    job_title: str
    reference_number: str | None = None
    institution: str | None = None

    # Consolidated primitives
    requirements: list[JobRequirement]
    themes: list[JobTheme]
    constraints: list[JobConstraint]
    responsibilities: list[str]

    # Read-between-lines risk signals
    risk_areas: list[str] = Field(
        default_factory=list,
        description="Signals that may reduce candidate fit"
    )
```

## 3) Input contract

Extracting nodes usually consume raw text and optional formatting constraints.

```python
from pydantic import BaseModel, Field


class ExtractingInput(BaseModel):
    job_id: str
    source_text_md: str = Field(..., description="Raw job text in Markdown")

    # Optional strict formatting constraints for JSON shape
    # formatting_constraints: StyleProfile | None = None
```

## 4) `logic.py` integration

Following the LLM boilerplate and Jinja prompt contract:

```python
from pathlib import Path


def run_logic(
    logic_input: ExtractingInput,
    runtime: LLMRuntime,
    prompt_bundle: PromptBundle,
) -> JobUnderstandingExtract:
    user_prompt = render_user_template(
        prompt_dir=Path("prompt"),
        template_name="user_template.md",
        payload=logic_input.model_dump(),
    )

    return runtime.generate_structured(
        system_prompt=prompt_bundle.system_prompt,
        user_prompt=user_prompt,
        output_schema=JobUnderstandingExtract,
    )
```

Design contract:

1. `user_template.md` variables must match `ExtractingInput` field names.
2. runtime must return schema-valid `JobUnderstandingExtract`.
3. markdown output, if any, is stored via Data Plane writers, not inside this JSON envelope.

## 5) Future extension: profile normalization from `profile.md`

Proposed extension:

- add an extracting flow that parses `profile.md` into structured `ProfileEvidence` blocks,
- normalize profile evidence IDs and categories to align with matching contracts,
- make profile extraction outputs structurally parallel to requirement extraction outputs.

Expected benefit:

- closer shape parity between job requirements and profile evidence,
- lower ambiguity in matching logic,
- easier deterministic validation of coverage claims.
