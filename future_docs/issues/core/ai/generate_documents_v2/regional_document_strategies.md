# generate_documents_v2: Regional Document Strategies Are Still Generic

**Why deferred:** The current v2 pipeline can assemble generic Markdown documents, but market-specific behavior needs explicit strategy selection, new contracts, and render-aware rules.
**Last reviewed:** 2026-04-03

## Problem / Motivation

The old generate-documents specs described country- and market-specific behavior such as German/DIN 5008 structure, academic variants, and region-aware section logic. The current implementation in `src/core/ai/generate_documents_v2/` does not implement those strategies yet.

Today the pipeline is closer to:

- generic profile loading
- generic blueprinting
- generic drafting
- generic Markdown assembly

This means the docs should not promise market-aware formatting or selection logic that is not actually present.

## Proposed Direction

- Add an explicit document strategy layer that selects rules by market/document context.
- Keep strategy selection separate from rendering.
- Persist the chosen strategy in stage artifacts for auditability.

## Examples of deferred behavior

- DIN 5008 letter layout behavior
- academic vs industry document branching
- country-specific section ordering rules
- region-specific legal/profile fields

## Related code

- `src/core/ai/generate_documents_v2/graph.py`
- `src/core/ai/generate_documents_v2/contracts/`
- `src/core/ai/generate_documents_v2/nodes/assembly.py`
