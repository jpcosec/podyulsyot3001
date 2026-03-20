# Taxonomy Case: Reviewing Contracts (Decision and Assistance)

Related references:

- `docs/reference/contract_composition_framework.md`
- `plan/runtime/sync_json_md.md`
- `docs/policy/feedback_memory.md`
- `docs/runtime/graph_flow.md`

## Purpose

This document defines the reviewing-case contracts for two separate responsibilities:

1. deterministic decision parsing (`review/decision.md` -> `review/decision.json`),
2. optional LLM review assistance for extracting reusable feedback rules.

The key boundary is strict:

- deterministic review gates decide routing,
- LLM assistance never decides routing.

## 1) Domain primitives (decisions and learning)

```python
from pydantic import BaseModel, Field
from typing import Literal


class ReviewDirective(BaseModel):
    scope: Literal["local", "global"]
    directive_type: Literal["factual", "strategic", "stylistic", "structural", "process"]
    target: str = Field(..., description="Requirement id or section target")
    action: Literal["keep", "edit", "drop", "regenerate", "forbid"]
    normalized_rule: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ParsedDecision(BaseModel):
    block_id: str = Field(..., description="Reviewed block id, for example R1")
    decision: Literal["approve", "request_regeneration", "reject"]
    notes: str = Field(default="", description="Reviewer free text")
    directives: list[ReviewDirective] = Field(
        default_factory=list,
        description="Tagged directives parsed from notes"
    )


class FeedbackRule(BaseModel):
    rule: str = Field(..., description="Distilled rule for future prompts")
    tags: list[str] = Field(..., description="Domain tags, for example 'phd', 'academic'")
    confidence: float
```

## 2) Deterministic envelope (`DecisionEnvelope`)

This is the output contract produced by `sync_json_md.md_to_json(...)`.
No LLM is used in this conversion.

```python
from pydantic import BaseModel, Field


class DecisionEnvelope(BaseModel):
    """Deterministic parser output for `review/decision.json`."""

    node: str
    job_id: str
    round: int
    source_state_hash: str = Field(..., description="Prevents validating stale decisions")
    decisions: list[ParsedDecision]
    updated_at: str
```

Deterministic invariants:

1. `source_state_hash` must match current proposed state,
2. exactly one decision per block,
3. malformed directive tags fail closed,
4. parser output is routing-safe and reproducible.

## 3) LLM assistance envelope (`ReviewAssistEnvelope`)

After deterministic parsing, optional review-assistance nodes can analyze why proposals failed and suggest reusable rules.

Input:

```python
from pydantic import BaseModel


class ReviewAssistInput(BaseModel):
    job_id: str
    upstream_proposed_state: dict
    parsed_decisions: list[ParsedDecision]
```

Output:

```python
from pydantic import BaseModel, Field


class ReviewAssistEnvelope(BaseModel):
    """Output for LLM review-assistance nodes."""

    schema_version: str = "1.0"
    doc_type: str = "review_assistance"

    insights: list[str] = Field(..., description="Why the proposal failed or was weak")
    reusable_rules: list[FeedbackRule] = Field(..., description="Rules to persist into feedback memory")
```

Boundary rule:

- `ReviewAssistEnvelope` cannot approve/reject anything.
- only deterministic review nodes emit routing decisions.

## 4) End-to-end contract cycle

1. Extracting outputs job requirements.
2. Matching outputs requirement/evidence mappings.
3. Reviewer edits markdown decision surface.
4. Deterministic parser emits `DecisionEnvelope`.
5. Review-assistance LLM distills reusable `FeedbackRule` objects.
6. Future runs inject those rules in matching/redacting inputs.

This closes the learning loop without weakening review gate determinism.

## 5) Pending expansion

This document focuses on reviewing contracts around the matching stage first.
Equivalent worked cases for later review stages can be added with the same primitives and envelopes.
