# Standards Alignment Follow-Ups

**Why deferred:** The pipeline MVP shipped by prioritizing end-to-end wiring, but several files currently diverge from the repository's code and documentation standards and should be normalized in a follow-up pass.
**Last reviewed:** 2026-03-29

## Problem / Motivation

The current implementation has a few concrete mismatches with `docs/standards/`:

- `src/graph/__init__.py` mixes graph wiring, direct adapter calls, file I/O, packaging writes, and top-level state definitions in a single file. This conflicts with `docs/standards/code/basic.md` and `docs/standards/code/llm_langgraph_components.md`, which require clearer layer ownership and thin graph nodes.
- `src/ai/generate_documents/graph.py` reads approved match artifacts directly, performs persistence work inside the graph layer, and writes hand-typed emoji log tags instead of using `LogTag` from `src/shared/log_tags.py`.
- Public package surfaces are incomplete or broken: `src/ai/generate_documents/__init__.py` exports nothing, and `src/tools/render/__init__.py` imports from `src.render.*` instead of the actual package path. This conflicts with the public-surface rule in `docs/standards/code/basic.md`.
- Module READMEs are now partially stale relative to the implementation and orchestration decision. This conflicts with the documentation lifecycle rule in `docs/standards/docs/documentation_and_planning_guide.md`.

These do not block the current MVP path, but they should be tracked explicitly so the repo does not normalize drift from its own standards.

## Proposed Direction

- Split pipeline orchestration from per-node adapter/storage code so `src/graph/` contains graph assembly and thin wrappers, while persistence stays in storage-oriented modules.
- Move `generate_documents` disk reads/writes fully behind storage interfaces and replace literal tag strings with `LogTag` usage.
- Export stable public entrypoints from module `__init__.py` files and update callers to use those surfaces instead of deep implementation imports where practical.
- Refresh the affected READMEs in the same pass so architecture, CLI, and data-contract descriptions match the code.

## Linked TODOs

- `src/graph/__init__.py` — `# TODO(future): split pipeline orchestration from adapter/file-IO code so nodes stay thin and storage-aware — see future_docs/issues/standards_alignment_followups.md`
- `src/ai/generate_documents/graph.py` — `# TODO(future): move match/document artifact reads and writes behind storage helpers and replace literal log tags with LogTag — see future_docs/issues/standards_alignment_followups.md`
- `src/cli/main.py` — `# TODO(future): route unified CLI through stable module entrypoints instead of deep internal imports where packages expose a public surface — see future_docs/issues/standards_alignment_followups.md`
- `src/ai/generate_documents/__init__.py` — `# TODO(future): expose the public generate_documents entrypoints required by external callers — see future_docs/issues/standards_alignment_followups.md`
- `src/tools/render/__init__.py` — `# TODO(future): fix and stabilize the public render package imports to match the real package layout — see future_docs/issues/standards_alignment_followups.md`
- `src/ai/match_skill/README.md` — `# TODO(future): update the module README so the graph flow no longer describes generate_documents as embedded in match_skill — see future_docs/issues/standards_alignment_followups.md`
- `src/ai/generate_documents/README.md` — `# TODO(future): update the module README to match the standalone graph/runtime role and current storage layout — see future_docs/issues/standards_alignment_followups.md`
- `src/review_ui/README.md` — `# TODO(future): update the review UI README to match the implemented imports, CLI path, and bus contract — see future_docs/issues/standards_alignment_followups.md`
