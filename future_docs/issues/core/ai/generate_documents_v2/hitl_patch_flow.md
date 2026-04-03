# generate_documents_v2: Rich HITL Patch Flow Is Not Implemented Yet

**Why deferred:** The graph already pauses at review points, but a real document-generation-specific edit/patch loop needs dedicated UI contracts and persistence behavior.
**Last reviewed:** 2026-04-03

## Problem / Motivation

The current `generate_documents_v2` graph has review pauses, and the CLI can auto-approve them, but there is no complete generate-documents-specific patch workflow equivalent to what the old specs described.

Missing pieces include:

- review payload shape for content/blueprint edits
- patch application semantics
- persistence of reviewer edits into artifacts
- a dedicated review UI flow for generate-documents artifacts

## Proposed Direction

- Define a concrete review payload contract for each pause point.
- Implement deterministic patch application per stage.
- Only document stage-specific review capabilities once they are actually wired into the UI/runtime.

## Related code

- `src/core/ai/generate_documents_v2/graph.py`
- `src/core/ai/generate_documents_v2/contracts/hitl.py`
- `src/review_ui/`
