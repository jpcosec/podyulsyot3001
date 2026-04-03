# generate_documents_v2: Extension Seams Are Not Stable Enough To Document As Public

**Why deferred:** The module is still evolving quickly, so extension guidance would drift unless the customization seams are formalized first.
**Last reviewed:** 2026-04-03

## Problem / Motivation

Older docs described clean extension points for countries, strategies, matching behavior, and style rules. The current implementation does not yet expose those seams as stable public extension interfaces.

Right now, most changes still require direct edits in:

- `src/core/ai/generate_documents_v2/contracts/`
- `src/core/ai/generate_documents_v2/nodes/`
- `src/core/ai/generate_documents_v2/subgraphs/`
- `src/core/ai/generate_documents_v2/prompts/`

## Proposed Direction

- Identify which extension surfaces are intended to be stable.
- Separate internal implementation detail from supported extension points.
- Only write an extension guide after those seams are explicit in code.

## Related code

- `src/core/ai/generate_documents_v2/README.md`
- `src/core/ai/generate_documents_v2/contracts/`
