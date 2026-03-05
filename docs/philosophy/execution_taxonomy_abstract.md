# Execution Taxonomy (Abstract)

Related references:

- `docs/architecture/structure_and_rationale.md`
- `docs/architecture/smart_template_discipline.md`
- `docs/architecture/core_io_and_provenance_manager.md`

## Purpose

This document defines the PhD 2.0 taxonomy at an abstract level, before binding categories to concrete nodes or subgraphs.

It is the classification system used to derive template behavior.

## Core principle

Classification is multi-axis, not single-axis.

A step is not fully described by "deterministic vs non-deterministic" alone.

## Axis A: LLM usage (primary)

First classify whether the step uses an LLM:

- `LLM-based`
- `Non-LLM-based`

This is the highest-priority boundary for architecture and risk control.

## Axis B: execution predictability (secondary)

Applied only to `Non-LLM-based` steps:

- `deterministic`: same inputs, same outputs under fixed environment.
- `non_deterministic_bounded`: no LLM, but output may vary due to external dependencies (network/API/backend drift).

Important:

- Non-LLM non-deterministic is still non-LLM. It must not be treated as generative/semantic LLM behavior.

## Axis C: LLM task intent

Applied only to `LLM-based` steps:

- `extracting`: distill/normalize into structured machine state.
- `matching`: map requirements to evidence and estimate coverage.
- `reviewing`: interpret review content as assistance output (non-gating).
- `redacting`: draft narrative text/content for human review.

Important:

- `reviewing` as an LLM task intent is not the same as deterministic approval-gate parsing.

## Axis D: gate role (approval semantics)

Applied to all steps:

- `review_gated`: execution must pause for HITL decision.
- `non_gated`: step continues automatically on success.

This axis is orthogonal to LLM usage.

## Canonical taxonomy tree (high-level)

```text
execution
├── llm-based
│   ├── extracting
│   ├── matching
│   ├── reviewing
│   └── redacting
└── no-llm-based
    ├── deterministic
    └── non_deterministic_bounded
```

## Classification tuple

Every step should be represented as a tuple:

`(llm_usage, predictability_class, llm_intent, gate_role)`

Rules:

1. `predictability_class` is required only when `llm_usage = no-llm-based`.
2. `llm_intent` is required only when `llm_usage = llm-based`.
3. `gate_role` is always required.

## Why this abstraction matters

This abstract taxonomy drives template discipline and prevents category mistakes such as:

1. treating external non-LLM variability as LLM semantics,
2. allowing LLM review helpers to replace deterministic gate parsing,
3. applying retry policy from one category to an incompatible category,
4. introducing GraphState payload bloat due to unclear step semantics.

## Out of scope

This document intentionally does not assign concrete nodes or define subgraph composition.

Those mappings are handled in architecture documents that consume this taxonomy.
