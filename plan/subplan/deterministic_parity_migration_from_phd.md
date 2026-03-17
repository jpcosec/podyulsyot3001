# Deterministic Parity Migration from `phd` to `phd2-empty`

Date: 2026-03-12

## Purpose

Complete the migration of deterministic behavior from `/home/jp/phd-workspaces/phd` into this rebuild workspace, keeping PhD 2.0 contracts, HITL gates, and fail-closed behavior as the primary constraints.

This document is implementation planning only (no runtime code changes).

## Scope

In scope:

1. Deterministic logic, validators, parsers, render/packaging, and deterministic orchestration helpers.
2. Deterministic review infrastructure for all review nodes, not only `review_match`.
3. Deterministic data-plane I/O centralization (`core/io` target architecture).

Out of scope:

1. Prompt redesign and LLM semantic quality tuning.
2. Any change that weakens current fail-closed behavior.
3. Large topology rewrites before deterministic parity baselines are met.

## Current Baseline (Observed)

Already available in `phd2-empty`:

- `src/core/tools/scraping/` and `src/core/tools/translation/`.
- Render primitives in `src/core/tools/render/` (`docx.py`, `latex.py`, `pdf.py`, `letter.py`, `styles.py`).
- Match review rounds and regeneration plumbing (`src/core/round_manager.py`, `src/nodes/match/`, `src/nodes/review_match/`).
- Prep-match runtime CLI and checkpoint-aware resume (`src/cli/run_prep_match.py`).

Key deterministic gaps versus target architecture:

1. `core/io` layer (`WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, `ProvenanceService`) is still documented target, not implemented.
2. Full deterministic delivery chain (`render` and final `package` nodes in graph runtime) is not wired as active runtime path.
3. Deterministic review node family is complete only for `review_match`.
4. Cross-node deterministic artifact conventions are still partially inline in node logic.

## Legacy-to-Target Deterministic Inventory

Source candidates from legacy workspace (`/home/jp/phd-workspaces/phd`):

1. `src/render/{docx,latex,pdf,styles}.py` -> align with `src/core/tools/render/` as canonical deterministic rendering base.
2. `src/steps/rendering.py` -> split into deterministic render node orchestration + CLI wrappers.
3. `src/steps/packaging.py` and `src/utils/pdf_merger.py` -> deterministic package node and merge/compress helper service.
4. `src/utils/cv_rendering.py` deterministic subparts -> reusable context shaping, parity checks, path resolution (without bringing legacy pipeline coupling).

Migration rule:

- Port behavior, not architecture debt. Legacy modules are source material, not drop-in units.

## Work Packages

## WP1 - Core I/O and Provenance Foundation (Highest Priority)

Deliverables:

1. Implement `src/core/io/` service layer per `docs/architecture/core_io_and_provenance_manager.md`.
2. Replace inline artifact path handling in active nodes with reader/writer abstractions.
3. Enforce deterministic read/write contracts (no silent defaults for required inputs).

Acceptance:

- Existing prep-match tests still pass.
- At least one active node (`match` or `review_match`) runs exclusively through `core/io` adapters.

## WP2 - Deterministic Review Substrate Generalization

Deliverables:

1. Create shared deterministic review utilities usable by `review_application_context`, `review_motivation_letter`, `review_cv`, `review_email`.
2. Standardize stale-hash checking, parse errors, and route precedence semantics.
3. Standardize round history persistence layout for all review-capable nodes.

Acceptance:

- Shared deterministic parser/service passes unit tests for all three outcomes: `approve`, `request_regeneration`, `reject`.

## WP3 - Deterministic Delivery Chain Completion

Deliverables:

1. Implement graph-visible `render` node with deterministic outputs and provenance entries.
2. Implement graph-visible `package` node with deterministic merge/compress manifest semantics.
3. Ensure prep/full runtime separation is explicit (active path vs target path).

Acceptance:

- End-to-end deterministic delivery run produces expected artifacts in `data/jobs/<source>/<job_id>/application/`.

## WP4 - Deterministic Observability and Quality Gates

Deliverables:

1. Deterministic per-node execution metadata (`started_at`, `ended_at`, status, error_type`) in node `meta/` artifacts.
2. Deterministic output parity checks for render outputs where applicable.
3. Operator-facing run summary artifact for each job.

Acceptance:

- One job can be audited without reading LangGraph checkpoint internals.

## Execution Order

1. WP1 `core/io`
2. WP2 review substrate
3. WP3 render/package completion
4. WP4 observability hardening

Rationale:

- `core/io` reduces churn and lets later work land with stable path/provenance contracts.

## Risks and Controls

1. Risk: legacy module coupling leaks into rebuild.
   Control: isolate legacy code into small imported functions and refactor to current contracts.
2. Risk: deterministic migration accidentally changes active prep-match behavior.
   Control: preserve prep-match regression suite as non-negotiable gate.
3. Risk: render/package deterministic details become CLI-only utilities again.
   Control: require graph-visible node contracts first, CLI wrappers second.

## Definition of Done

1. All deterministic target services listed in this document exist under `src/core/` and are test-covered.
2. Full-path deterministic nodes (`render`, `package`, review parsers) are contract-driven and fail closed.
3. Active runtime and target runtime docs are both updated and aligned with implemented behavior.
