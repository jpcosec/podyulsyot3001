# generate_documents_v2: Audit Remaining Semantics From The Old `extract_understand` Node

**Why deferred:** The old dev-branch `extract_understand` node should not be ported as a monolithic node, but some of the semantics it carried may still deserve explicit coverage in the current staged pipeline.
**Last reviewed:** 2026-04-03

## Context

The old dev-branch shape was:

```text
raw_text -> extract_understand -> JobUnderstandingExtract
```

The current pipeline is intentionally split into narrower typed stages:

```text
raw job surfaces -> ingestion -> JobKG
JobKG -> requirement_filter -> JobDelta
ProfileKG + JobKG -> alignment -> MatchEdge[]
```

That architectural shift is correct. The open question is not whether to restore `extract_understand`, but whether any of its useful semantics were dropped during the split.

## Semantics worth auditing

### 1. Contact extraction richness

Current state:

- `JobKG.company.contact_person` exists
- prompts mention contact person extraction

Audit question:

- do we need richer contact capture than a single `contact_person` field?
- is there value in preserving multiple contacts or typed contact methods?

### 2. Salary and pay-grade capture

Current state:

- ingestion prompts mention salary / teaser salary
- `JobKG` does not currently expose a first-class salary or pay-grade field

Audit question:

- should salary or grade information become an explicit contract field rather than staying implicit in raw text or anchors?

### 3. Constraint and risk modeling

Current state:

- `JobKG.logistics` captures location/remote/contract/relocation/visa
- no first-class `constraints` or `risk_areas` collections exist

Audit question:

- are there recurring job constraints that should become structured fields?
- do document-generation stages benefit from explicit risk-area modeling?

### 4. Source anchoring quality

Current state:

- `JobKG.source_anchors` exists via `TextAnchor`

Audit question:

- does current anchoring cover the old need for requirement-level text spans well enough?
- if not, should `JobRequirement` carry direct anchor references?

### 5. Extraction rationale

Current state:

- no explicit `analysis_notes` equivalent is exposed in `JobKG`

Audit question:

- do we need an auditable extraction rationale field, or are persisted stage artifacts sufficient?

## Recommendation

Do not revive the old monolithic `extract_understand` node.

Instead:

1. audit `JobKG` and `JobDelta` against the semantic gaps above
2. promote only the missing high-value fields into the current contracts
3. keep extraction, filtering, and alignment as separate stages

## Related code

- `src/core/ai/generate_documents_v2/contracts/job.py`
- `src/core/ai/generate_documents_v2/nodes/ingestion.py`
- `src/core/ai/generate_documents_v2/nodes/requirement_filter.py`
- `src/core/ai/generate_documents_v2/nodes/alignment.py`
- `src/core/ai/generate_documents_v2/prompts/ingestion.py`
