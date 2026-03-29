# Testing Strategy & Data Management

**Why deferred:** The `generate_documents` node reads from disk paths (`output/match_skill/...`) that are not yet defined by a stable data management contract. Tests that cross module boundaries cannot be written deterministically until output paths, artifact ownership, and test fixture conventions are settled.
**Last reviewed:** 2026-03-29

---

## Problem / Motivation

The current test for `run_match_skill` fails on the resume path because `generate_documents` tries to read approved match artifacts from a hardcoded disk path (`output/match_skill/<source>/<job_id>/...`) rather than from state or a fixture. This reveals a broader gap: there is no agreed contract for:

- Where each module writes its artifacts (who owns which directory).
- How tests provide artifact fixtures across module boundaries.
- Whether integration tests hit the real disk layout or inject via state.

Without this, any test that crosses the `match_skill → generate_documents` boundary is fragile.

## Proposed Direction

### 1. Define data management contract

Establish a single document (e.g. `docs/runtime/data_management.md`) that specifies:
- The canonical output directory tree for each module.
- Which module owns each path (writer) and which reads it (consumer).
- How artifact paths are resolved — through state refs, a path registry, or a shared store.

### 2. Test fixture conventions

Once paths are stable, define how tests provide cross-module fixtures:
- Option A: Integration tests write real artifacts into `tmp_path` and pass `output_dir` consistently across both modules.
- Option B: Nodes accept injected stores so tests can mock artifact reading without touching disk.

Option B (store injection) is already partially implemented — `MatchArtifactStore` is injectable. `DocumentArtifactStore` and `MatchArtifactStore` reads inside `src/generate_documents/graph.py` are currently hardcoded and need to be injected too.

### 3. Fix generate_documents node hardcoded paths

`_make_generate_documents_node` in `src/generate_documents/graph.py` (line ~128) constructs a `MatchArtifactStore()` with no root argument, defaulting to `output/match_skill`. This bypasses any `output_dir` passed to the CLI. The store should be injected, consistent with how `match_skill` handles it.

---

## Linked TODOs

- `src/generate_documents/graph.py` — at `_make_generate_documents_node`: `# TODO(future): inject MatchArtifactStore instead of constructing with default root — see future_docs/testing_and_data_management.md`
- `tests/` — `# TODO(future): define cross-module fixture conventions — see future_docs/testing_and_data_management.md`
