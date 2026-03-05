# Graph Definition and Node Contracts

Related references:

- `docs/graph/node_io_matrix.md`
- `docs/philosophy/structure_and_rationale.md`

## Purpose

This document defines the intended graph flow, review branch semantics, and the minimum contract expectations per node.

It is the operational architecture reference for implementation and review.

## Canonical graph flow

Primary path:

1. `scraping` (pre-graph preparation)
2. `ingest`
3. `extract_understand`
4. `translate`
5. `match`
6. `review_match`
7. `build_application_context`
8. `review_application_context`
9. `generate_motivation_letter`
10. `review_motivation_letter`
11. `tailor_cv`
12. `review_cv`
13. `draft_email`
14. `review_email`
15. `render`
16. `package`

## Canonical macro-node composition (subgraphs)

The same flow should be represented in LangGraph as phase subgraphs (macro-nodes) to keep the top-level graph readable:

1. `prep_subgraph`: `ingest -> extract_understand -> translate`
2. `match_cycle_subgraph`: `match -> review_match` (+ regeneration loop)
3. `context_cycle_subgraph`: `build_application_context -> review_application_context` (+ regeneration loop)
4. `motivation_cycle_subgraph`: `generate_motivation_letter -> review_motivation_letter` (+ regeneration loop)
5. `cv_cycle_subgraph`: `tailor_cv -> review_cv` (+ regeneration loop)
6. `email_cycle_subgraph`: `draft_email -> review_email` (+ regeneration loop)
7. `delivery_subgraph`: `render -> package`

Top-level orchestration may then be expressed as:

`scraping -> prep_subgraph -> match_cycle_subgraph -> context_cycle_subgraph -> motivation_cycle_subgraph -> cv_cycle_subgraph -> email_cycle_subgraph -> delivery_subgraph`

Design rule:

- subgraph boundaries are functional phases; internal nodes remain explicit for auditability and retry semantics.

## Review branch semantics

For each review node:

- `approve` -> continue with approved artifact.
- `request_regeneration` -> loop to generation node.
- `reject` -> terminate current run.

The runtime must emit the routing decision explicitly and log it in run metadata.

## Graph checkpoints and resume

Resume points exist at review interrupts.

Checkpoint invariants:

1. run id must match checkpoint context,
2. pending node/gate must match graph status,
3. decision artifact must validate against the active proposed state hash.

If invariant checks fail, resume must stop with an actionable error.

## Node contract expectations

Every node package should provide:

- `contract.py`: typed input/output schema.
- `logic.py`: node behavior only.
- `node.py`: orchestration entrypoint.
- `prompt/`: node-local prompt assets for LLM nodes.

I/O read/write concerns are centralized in `src/core/io/`.

## Deterministic node definitions

## `ingest`

- reads: legacy/source raw artifacts.
- writes: normalized ingest state in `proposed` and `approved`.
- purpose: establish canonical input base.

## `extract_understand`

- reads: ingested raw/extracted source.
- writes: structured understanding (requirements/themes/responsibilities/constraints).
- purpose: produce stable machine-readable job understanding.

## `translate`

- reads: extracted understanding.
- writes: translated fields and language metadata.
- purpose: normalize language for downstream AI nodes.

## `review_match`, `review_application_context`, `review_motivation_letter`, `review_cv`, `review_email`

- reads: proposed state + decision markdown.
- writes: decision json + approved state + provenance.
- purpose: enforce HITL decisions with deterministic parsing.

## `review_cv`

- reads: `tailor_cv` proposed state + CV draft markdown + decision markdown.
- writes: decision json + approved CV state/markdown + provenance.
- purpose: validate CV before downstream email/render/package.

## `review_email`

- reads: `draft_email` proposed state + email draft markdown + decision markdown.
- writes: decision json + approved email state/markdown + provenance.
- purpose: validate final email content before delivery.

## `render`

- reads: approved CV and motivation artifacts.
- writes: real render outputs and state metadata.
- purpose: generate deliverable files.

## `package`

- reads: rendered outputs.
- writes: final package artifact + manifest + provenance.
- purpose: finalize submission bundle.

## LLM node definitions

## `match`

- reads: translated understanding and profile context.
- writes: requirement-claim mapping proposal and review surface.
- purpose: map candidate evidence to job requirements.

## `build_application_context`

- reads: approved match mapping and profile constraints.
- writes: approved-claim context for writing nodes.
- purpose: define positioning strategy and claim set.

## `generate_motivation_letter`

- reads: approved application context.
- writes: motivation draft + claim consumption refs + review surface.
- purpose: create job-specific motivation narrative.

## `tailor_cv`

- reads: approved context and reviewed motivation.
- writes: render-ready tailored CV markdown/state.
- purpose: produce CV aligned to approved strategy.

## `draft_email`

- reads: approved context and reviewed motivation.
- writes: application email draft state/artifact.
- purpose: produce concise, job-specific submission email.

## LLM task taxonomy (prompt-level)

For LLM-driven work, task intent is classified into exactly one category:

- `extracting`: distill or normalize source semantics into structured state.
- `matching`: map requirements to evidence and estimate coverage.
- `reviewing`: interpret review content as assistance tasks (non-gating).
- `redacting`: draft candidate narrative/content for human review.

### Task classification list

| Task | Category | Notes |
| --- | --- | --- |
| `matcher` | `matching` | Requirement-to-evidence mapping and claim proposals. |
| `application_context_builder` | `extracting` | Distills approved mapping into shared downstream context. |
| `motivation_letter_writer` | `redacting` | Drafts letter narrative for review. |
| `cv_tailorer` | `redacting` | Drafts CV content and ordering for review. |
| `email_drafter` | `redacting` | Drafts concise application email for review. |
| `match_review_parser` | `reviewing` | Review interpretation helper; not a gating source of truth. |
| `motivation_letter_review_parser` | `reviewing` | Review interpretation helper; not a gating source of truth. |
| `cv_review_parser` | `reviewing` | Review interpretation helper; not a gating source of truth. |
| `email_review_parser` | `reviewing` | Review interpretation helper; not a gating source of truth. |
| `feedback_distiller` | `extracting` | Distills feedback events into reusable active-memory rules. |

Note: this taxonomy classifies prompt task intent, not runtime gate authority. Runtime safety class is defined by LLM usage and non-LLM determinism class; approval gate parsing remains deterministic.

## Artifact path conventions

Per node:

- `nodes/<node>/proposed/state.json` is canonical machine proposal.
- `nodes/<node>/proposed/view.md` is reviewer-readable mirror.
- `nodes/<node>/review/decision.md` is human edit surface.
- `nodes/<node>/review/decision.json` is parser output.
- `nodes/<node>/approved/state.json` is canonical approved state.
- `nodes/<node>/meta/provenance.json` is trace metadata.

Project-level:

- `raw/` source artifacts,
- `runtime/checkpoints/` graph resume metadata,
- `final/` deliverables and manifest.

## Review directive format

Review decision files (`review/decision.md`) support structured directives that convert reviewer notes into machine-usable semantics.

### Rule

- Free text in notes is never auto-interpreted into policy semantics.
- Only explicitly tagged note directives are converted to structured fields.

### Directive format (v1)

```text
@scope: local|global
@type: factual|strategic|stylistic|structural|process
@target: <req_id|node_field>
@action: keep|edit|drop|regenerate|forbid
@normalized_rule: <explicit reusable rule>
@confidence: <0..1>
```

### Parsing rules

- Tagged directives are converted to deterministic structured fields in `decision.json`.
- Untagged notes are preserved as raw text only — no semantic extraction.
- Missing required directive keys result in a validation error.

See `docs/business_rules/claim_admissibility_and_policy.md` for full admissibility rules and `docs/business_rules/sync_json_md.md` for parser behavior.

## Non-negotiable graph invariants

1. Downstream nodes consume only approved upstream artifacts.
2. Review parsers fail closed on malformed decisions.
3. Stale hash mismatch always blocks continuation.
4. No node may return success using placeholder fallback generation.
5. Every approved artifact in critical path carries provenance.
