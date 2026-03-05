# Documentation Pruning Plan

This plan keeps the current migration safe while reducing drift over time.

## Phase 1 (completed)

1. Introduce canonical concept folders.
2. Use temporary compatibility aliases during transition.
3. Publish canonical index and conceptual tree.

## Phase 2 (completed)

1. Updated internal links in canonical docs to canonical paths.
2. Removed compatibility alias files once migration stabilized.
3. Added index-level governance docs (`canonical_map`, `conceptual_tree`, `pruning_plan`).

## Phase 3 (future hardening)

1. Add checks that reject references to deprecated paths in docs.
2. Add optional front matter metadata (`status`, `canonical_for`, `owner`) to canonical docs.
3. Keep migration notes in `changelog.md` and docs index governance files.

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
