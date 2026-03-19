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

---

## Execution Annex (added 2026-03-19)

### A. File-Level Migration Matrix

#### Already migrated (no action needed)

| Legacy file | Rebuild target | Status |
|---|---|---|
| `src/render/docx.py` | `src/core/tools/render/docx.py` | Identical copy |
| `src/render/styles.py` | `src/core/tools/render/styles.py` | Identical copy |
| `src/render/latex.py` | `src/core/tools/render/latex.py` | Compatible refactor (`compile_cv_pdf` added, `_latex_safe` improved) |
| `src/render/pdf.py` | `src/core/tools/render/pdf.py` | Compatible refactor (better fallback chain) |
| — | `src/core/tools/render/letter.py` | New in rebuild (motivation letter renderer) |

#### Pending migration (WP3 scope)

| Legacy file | Rebuild target | Strategy |
|---|---|---|
| `src/steps/rendering.py` (444 lines) | `src/nodes/render/logic.py` + `src/nodes/render/contract.py` | Decompose into node contract + logic; extract `_render_cv`, `_render_motivation_letter`, `validate_ats` |
| `src/steps/packaging.py` (250 lines) | `src/nodes/package/logic.py` + `src/nodes/package/contract.py` | Decompose into node contract + logic; extract `_merge_pdfs`, `_compress_pdf` |
| `src/utils/pdf_merger.py` (74 lines) | `src/core/tools/pdf.py` | Refactor `merge_pdfs`, `compress_pdf` as deterministic service functions |
| `src/utils/cv_rendering.py` (837 lines) | Split across: `src/core/io/` (path resolution), `src/nodes/render/logic.py` (orchestration), `src/core/tools/render/` (render calls), `src/cli/` (CLI entry) | Largest file; needs decomposition — port behavior only, not coupling |

#### Pending implementation (WP1 scope — no legacy equivalent)

| Rebuild target | Source reference |
|---|---|
| `src/core/io/workspace_manager.py` | `docs/architecture/core_io_and_provenance_manager.md` spec |
| `src/core/io/artifact_reader.py` | Same spec |
| `src/core/io/artifact_writer.py` | Same spec |
| `src/core/io/provenance_service.py` | Same spec |

#### Legacy tests to port

| Legacy test | Rebuild target | WP |
|---|---|---|
| `tests/render/test_docx.py` | `tests/core/tools/render/test_docx.py` | WP3 |
| `tests/render/test_pdf.py` | `tests/core/tools/render/test_pdf.py` | WP3 |
| `tests/steps/test_matching.py` | Consolidate into `tests/nodes/match/` (partial overlap) | WP2 |
| `tests/steps/test_motivation.py` | `tests/nodes/generate_documents/` (partial overlap) | WP3 |
| `tests/steps/test_cv_tailoring.py` | `tests/nodes/generate_documents/` (partial overlap) | WP3 |
| `tests/cv_generator/test_model.py` | `tests/nodes/generate_documents/test_contract.py` (partial overlap) | WP3 |

### B. Test Gates per Work Package

Each WP has a mandatory gate command. The WP is not done until the gate passes.

#### WP1 — Core I/O and Provenance Foundation

```bash
# Gate: new core/io tests + existing prep-match regression
python -m pytest tests/core/io/ -q
python -m pytest tests/core/ tests/nodes/match/ tests/nodes/review_match/ tests/cli/test_run_prep_match.py -q
```

Pilot node: `match` or `review_match` — must run exclusively through `core/io` adapters.

#### WP2 — Deterministic Review Substrate

```bash
# Gate: shared review utilities pass all three outcomes
python -m pytest tests/core/review/ -q
# Gate: existing review_match regression
python -m pytest tests/nodes/review_match/ -q
```

#### WP3 — Deterministic Delivery Chain

```bash
# Gate: render/package nodes + ported legacy tests
python -m pytest tests/core/tools/render/ tests/nodes/render/ tests/nodes/package/ -q
# Gate: full suite still green
python -m pytest tests/ -q
```

#### WP4 — Observability and Quality Gates

```bash
# Gate: metadata/provenance service tests
python -m pytest tests/core/io/ tests/core/observability/ -q
# Gate: full suite still green
python -m pytest tests/ -q
```

### C. Rollback Protocol

1. **Before each WP slice**: tag the current state: `git tag pre-wp{N}-{slice_name}`.
2. **After each slice commit**: run the WP gate command. If it fails:
   - Do NOT proceed to the next slice.
   - Fix in the same branch. If the fix is non-trivial (>30 min), revert to the tag: `git reset --hard pre-wp{N}-{slice_name}`.
3. **Cross-WP regression**: if a later WP breaks an earlier WP gate, the later WP is rolled back first.
4. **Full-suite regression**: `python -m pytest tests/ -q` is the final gate before any WP is considered done. No exceptions.

### D. Commit Slicing Policy

1. **One commit per logical migration unit** (single file or tightly coupled pair).
2. **Maximum 4 files per commit** unless all files are in the same module and inseparable.
3. **Test file always in the same commit** as its implementation.
4. **Never commit a migration slice without running its WP gate first.**
5. **Changelog entry per WP completion** (not per commit) with exact verification steps.

### E. Execution Checklist

- [ ] **WP1-1**: Implement `src/core/io/__init__.py`, `workspace_manager.py`, `artifact_reader.py`, `artifact_writer.py`
- [ ] **WP1-2**: Implement `provenance_service.py`
- [ ] **WP1-3**: Convert `match` node to use `core/io` adapters
- [ ] **WP1-4**: Convert `review_match` node to use `core/io` adapters
- [ ] **WP1-gate**: Run WP1 test gate — must pass
- [ ] **WP2-1**: Extract shared review utilities from `review_match` into `src/core/review/`
- [ ] **WP2-2**: Add unit tests for approve/reject/request_regeneration paths
- [ ] **WP2-3**: Wire `review_application_context`, `review_motivation_letter`, `review_cv`, `review_email` stubs
- [ ] **WP2-gate**: Run WP2 test gate — must pass
- [ ] **WP3-1**: Port `src/utils/pdf_merger.py` → `src/core/tools/pdf.py`
- [ ] **WP3-2**: Port legacy render tests → `tests/core/tools/render/`
- [ ] **WP3-3**: Implement `src/nodes/render/contract.py` + `logic.py`
- [ ] **WP3-4**: Implement `src/nodes/package/contract.py` + `logic.py`
- [ ] **WP3-5**: Decompose `src/utils/cv_rendering.py` into node logic + core tools
- [ ] **WP3-gate**: Run WP3 test gate — must pass
- [ ] **WP4-1**: Add per-node execution metadata to `meta/` artifacts
- [ ] **WP4-2**: Add operator-facing run summary artifact
- [ ] **WP4-gate**: Run WP4 test gate — must pass
- [ ] **Final gate**: `python -m pytest tests/ -q` — all green
