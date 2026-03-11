# Taxonomy Case: Matching Contracts (Matrix and Escape Hatch)

Related references:

- `docs/reference/contract_composition_framework.md`
- `docs/reference/extracting_contract_case_job_understanding.md`
- `docs/business_rules/sync_json_md.md`
- `docs/graph/nodes_summary.md`

## Purpose

This document specifies a concrete matching-case contract where the matcher output is modeled as a requirement/evidence matrix and rendered into a review surface with a deterministic escape hatch.

Scope:

1. matching primitives for matrix evaluation,
2. `MatchEnvelope` output contract,
3. `MatchingInput` input contract,
4. deterministic render/parse behavior for manual missing requirements.

## 1) Domain primitives (matrix)

Base primitives are preserved. This case adds matrix-specific primitives for matching.

```python
from pydantic import BaseModel, Field
from typing import Literal


class EvidenceEvaluation(BaseModel):
    evidence_id: str = Field(..., description="Evaluated evidence id, for example P_EXP_01")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Match strength from 0.0 to 1.0")
    reason_for_match: str | None = Field(None, description="Why this evidence supports the requirement")
    reason_against_match: str | None = Field(None, description="Limitations or mismatch rationale")


class RequirementMapping(BaseModel):
    req_id: str
    requirement_text: str
    coverage_status: Literal["full", "partial", "none"]
    evaluated_evidence: list[EvidenceEvaluation]
    risk_flags: list[str] = Field(default_factory=list)
```

## 2) Taxonomy envelope (`MatchEnvelope`)

For `match` (`proposed/state.json`), output must carry a pointer to original source text so review rendering can include the context mirror.

```python
from pydantic import BaseModel, Field


class MatchEnvelope(BaseModel):
    """Output contract for `match` (`proposed/state.json`)."""

    schema_version: str = "1.0"
    doc_type: str = "match_proposal"

    # critical for review renderer
    source_text_ref: str = Field(..., description="Path to raw/source_text.md")

    mappings: list[RequirementMapping]
    proposed_claims: list[dict]
    unmapped_evidence_ids: list[str]
```

Design rule:

- `source_text_ref` is mandatory in matching output.

## 3) Input contract (`MatchingInput`)

The matcher receives requirements, profile evidence, and active feedback memory.

```python
from pydantic import BaseModel, Field


class MatchingInput(BaseModel):
    job_id: str
    source_text_ref: str
    job_requirements: list[JobRequirement]
    profile_evidence: list[ProfileEvidence]
    active_feedback: list[FeedbackRule] = Field(default_factory=list)
```

Design rule:

- `source_text_ref` passes through from input to output so renderer can always reach original raw context.

## 4) Render contract (`sync_json_md`: JSON -> Markdown)

For `match` review surfaces (`review/decision.md`), deterministic rendering should include:

1. front matter with `source_state_hash` and node id,
2. a collapsed "rear-view mirror" section with original source text loaded from `source_text_ref`,
3. matrix blocks per requirement with decisions,
4. an explicit manual escape hatch for missing requirements.

Reference layout:

```markdown
---
source_state_hash: "sha256:abc123..."
node: "match"
---

# Rear-view Mirror (Original Context)
> [!info]- View original posting text
> (Renderer injects content of `raw/source_text.md` via `source_text_ref`, collapsed by default.)

# Evaluation Matrix

### Requirement: R1 (Python experience)
| Evidence | Score | Reason for match | Limitations |
|----------|-------|------------------|-------------|
| P_EXP_02 | 0.9   | Used Python...   | None        |
| P_EDU_01 | 0.4   | Basic course     | No prod use |
**Decision:** [ ] approve  [ ] request_regeneration  [ ] reject
**Notes:**

# Escape Hatch: Missing Requirements
If a critical requirement was omitted, add it here to force matcher regeneration.

### Manual Requirement: New
**Requirement text:**
**Priority:** [ ] must  [ ] nice
```

## 5) Parse contract (`sync_json_md`: Markdown -> JSON)

When operator fills the manual requirement block, deterministic parser behavior is:

1. detect non-empty manual requirement text,
2. create a normalized requirement patch entry (for example id `R_MANUAL_01`),
3. persist patch artifact in review node space (recommended path: `nodes/review_match/meta/manual_requirements_patch.json`),
4. force routing output to `{"review_decision": "request_regeneration"}`.

Regeneration then returns flow to `match`, which must load approved requirements plus the patch and rebuild the matrix.

Important implementation note:

- prefer patch artifacts over in-place mutation of `extract_understand/approved/state.json` to preserve provenance and avoid hidden state rewrites.

## 6) UX and audit benefits

1. Reviewer sees the original source text alongside matrix decisions.
2. Missing-requirement recovery is explicit and deterministic.
3. Regeneration trigger is explainable and machine-verifiable.
4. Upstream approved artifacts remain immutable; manual additions are traceable patches.
