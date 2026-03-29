# Pipeline Unification Follow-Ups

**Why deferred:** The pipeline MVP is wired end-to-end, but a few contract and migration gaps are still being carried as implementation debt while the current orchestration path stabilizes.
**Last reviewed:** 2026-03-29

## Problem / Motivation

The current pipeline direction is mostly settled, but several items remain only partially covered by the active plans and implementation:

- `generate_documents` still constructs its own default-root stores instead of receiving the active runtime store/path contract explicitly.
- The top-level pipeline state still mixes orchestration concerns with shared contracts that were intended to move into `src/core/state.py` and `src/core/contracts.py`.
- The data-management contract exists in design prose, but not yet as a dedicated runtime reference that fixes path ownership, fixture conventions, and the cutover from the temporary `data/source` + `output/match_skill` split to the unified workspace.
- Cross-module tests exist, but the repository still lacks one explicit convention for whether boundary tests should use real `tmp_path` artifacts, injected stores, or both by default.

These are not Stage 7 hardening items. They are follow-up architecture and contract cleanup required to finish the non-future parts of pipeline unification cleanly.

## Proposed Direction

- Move shared top-level state types and reusable review/runtime contracts into `src/core/` so the pipeline graph stops being the implicit owner of those definitions.
- Inject the active match/document stores into `generate_documents` instead of constructing them internally with default roots.
- Write a dedicated runtime data-management doc that names the canonical workspace layout, path owners, readers, and testing conventions.
- Define the migration path from the temporary crossed directories to the target workspace as an explicit sequence, not just a target diagram.
- Make the test strategy explicit: module-pair tests should use `tmp_path` as the default integration path, while injected stores remain the mechanism for focused unit tests.

## Linked TODOs

- `src/graph/__init__.py` — `# TODO(future): move shared pipeline state/contracts into src/core and keep top-level state ref-oriented — see future_docs/issues/pipeline_unification_followups.md`
- `src/graph/nodes/extract_bridge.py` — `# TODO(future): replace temporary data/source -> output/match_skill path crossing with the canonical workspace contract — see future_docs/issues/pipeline_unification_followups.md`
- `src/ai/generate_documents/graph.py` — `# TODO(future): inject match/document stores from the pipeline runtime instead of constructing default-root stores here — see future_docs/issues/pipeline_unification_followups.md`
- `tests/e2e/test_pipeline.py` — `# TODO(future): lock the cross-module fixture convention around tmp_path integration artifacts vs injected stores — see future_docs/issues/pipeline_unification_followups.md`
- `docs/runtime/data_management.md` — `# TODO(future): document canonical pipeline path ownership, readers/writers, and test fixture conventions — see future_docs/issues/pipeline_unification_followups.md`
