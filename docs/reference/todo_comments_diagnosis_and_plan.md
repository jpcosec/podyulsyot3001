# TODO Comments Diagnosis and Plan

Date: 2026-03-11

## Scope

This document addresses only `#TODO` comments found in source code (`src/`) and does not include `data/`, `pipeline/`, or tests.

## Intent

Convert inline TODO notes into a clear implementation backlog before editing code.

## TODO Backlog (Current)

## 1) Graph topology clarity

1. `src/graph.py:2`  
   TODO: `IS THIS USING LANGRAPH?`  
   Diagnosis: stale/confusion comment; runtime already compiles/uses LangGraph interfaces.  
   Proposed action: replace with explicit module doc note that this file assembles the runtime graph and review transitions.  
   Priority: low.

2. `src/graph.py:21`  
   TODO: unclear `build_application_context -> review_application_context` step.  
   Diagnosis: implemented graph still contains target-architecture edges that are not currently in active prep-match runtime path.  
   Proposed action: document current active subgraph vs target edges directly near edge declarations and/or split constants into `ACTIVE_*` and `TARGET_*`.  
   Priority: high.

## 2) Extract-understand contract quality

3. `src/nodes/extract_understand/contract.py:21`  
   TODO: pre-ordering/sorting of extracted requirements.  
   Diagnosis: output ordering policy is implicit; risk of unstable diff/review behavior.  
   Proposed action: define deterministic ordering rule (e.g., by `priority`, then input order) and enforce in logic or post-validation step.  
   Priority: medium.

4. `src/nodes/extract_understand/contract.py:23`  
   TODO: add missing base fields (topic/tags/description/contact/form metadata).  
   Diagnosis: schema may be too narrow for downstream generation/routing and traceability.  
   Proposed action: decide minimal required fields for current runtime; add optional fields first to preserve backward compatibility.  
   Priority: high.

5. `src/nodes/extract_understand/contract.py:25`  
   TODO: non-English field description text.  
   Diagnosis: mixed language in schema docs hurts maintainability and team consistency.  
   Proposed action: standardize all contract descriptions/comments to English.  
   Priority: low.

## 3) Match contract and drift concerns

6. `src/nodes/match/contract.py:10`  
   TODO: requirement importance weighting/ranking.  
   Diagnosis: scoring lacks explicit requirement criticality dimension; harder decision transparency.  
   Proposed action: introduce optional `requirement_weight`/`importance` field and aggregate score policy; keep default compatibility.  
   Priority: medium.

7. `src/nodes/match/contract.py:19`  
   TODO: explain `_normalize_evidence_id`.  
   Diagnosis: helper behavior is correct but not obvious (string/list normalization).  
   Proposed action: add docstring with accepted shapes and reason for normalization.  
   Priority: low.

8. `src/nodes/match/contract.py:30`  
   TODO: possible drift between `MatchEnvelope` and real logic usage.  
   Diagnosis: potential contract/runtime mismatch risk.  
   Proposed action: verify all producers/consumers of `matched_data`; either enforce `MatchEnvelope` at write/read boundaries or remove dead schema fields.  
   Priority: high.

## 4) Review contract usage

9. `src/nodes/review_match/contract.py:10`  
   TODO: whether `ReviewDirective` is used.  
   Diagnosis: likely partially unused now; could be future-facing.  
   Proposed action: trace parser outputs and consumers; if unused, mark intentionally reserved or remove from envelope to reduce noise.  
   Priority: medium.

## 5) Extract-understand logic completeness

10. `src/nodes/extract_understand/logic.py:27`  
    TODO: missing crucial prompt info (e.g., job description context).  
    Diagnosis: prompt payload may omit useful context despite available ingested artifacts.  
    Proposed action: audit prompt template required tags vs provided node data and fill missing structured fields intentionally.  
    Priority: high.

11. `src/nodes/extract_understand/logic.py:37`  
    TODO: question about automatic Pydantic-driven mapping.  
    Diagnosis: explicit mapping is intentional for state safety/fail-closed validation.  
    Proposed action: keep explicit mapping, add short rationale comment/docstring, and remove misleading TODO.  
    Priority: low.

## 6) Rendering tooling notes

12. `src/core/tools/render/docx.py:16`  
    TODO: pydoc/template support.  
    Diagnosis: feature request mixed into code comment; not blocking runtime.  
    Proposed action: move to docs backlog; add concise module-level docs and defer template system until requirements are defined.  
    Priority: low.

13. `src/core/tools/render/latex.py:13`  
    TODO: move escapes to templates.  
    Diagnosis: current escape map is centralized and deterministic; template-level escaping could fragment logic.  
    Proposed action: keep central escaping for now; document why and revisit only if per-template behavior is needed.  
    Priority: low.

14. `src/cli/render_cv.py:23`  
    TODO: deterministic order should belong in core.  
    Diagnosis: architectural boundary concern is valid; CLI currently carries transformation logic.  
    Proposed action: extract context-building to core rendering service module and keep CLI as thin orchestration.  
    Priority: medium.

## Suggested Execution Order

1. High-priority architecture/runtime integrity items: #2, #4, #8, #10.
2. Contract/usage cleanup: #3, #6, #9, #14.
3. Documentation/clarity cleanup: #1, #5, #7, #11, #12, #13.

## Definition of Done (for this TODO pass)

- Every current `#TODO` in `src/` is either:
  - resolved in code and removed, or
  - converted into a tracked backlog item with owner/priority and removed from inline source.
- No ambiguous TODOs remain in hot-path runtime files (`graph.py`, `extract_understand`, `match`, `review_match`).
