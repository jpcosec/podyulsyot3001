# Documentation Pruning Plan

This plan keeps the current migration safe while reducing drift over time.

## Phase 1 (already active)

1. Introduce canonical concept folders.
2. Keep legacy locations as compatibility aliases.
3. Publish canonical index and conceptual tree.

## Phase 2 (recommended next)

1. Update internal links in canonical docs to point only to canonical paths.
2. Remove repeated policy paragraphs from non-canonical docs and replace with short links.
3. Add front matter metadata (`status`, `canonical_for`, `owner`) to canonical docs.

## Phase 3 (cleanup)

1. Add checks that prevent new substantive content in alias files.
2. Remove legacy aliases after two stable iterations.
3. Keep migration notes in `changelog.md` only.

## Split and merge recommendations

- Keep split:
  - `docs/philosophy/` vs `docs/graph/` vs `docs/templates/` vs `docs/business_rules/`.
- Merge candidate (future):
  - `docs/architecture/core_io_manager.md` into `docs/architecture/core_io_and_provenance_manager.md` once external references stop requiring alias.
- Keep prompts under templates:
  - `docs/templates/prompts/` is canonical for all prompt specs.

## Drift guardrails

1. New docs must be placed by concept first, not by historical folder.
2. Rules should be specified once and linked elsewhere.
3. Any moved canonical doc must be reflected in `docs/index/canonical_map.md`.
