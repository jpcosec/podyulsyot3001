# Automation Planning Docs

This folder is the planning-doc home for the browser automation worktree.

It holds the design notes that still matter for scraping, BrowserOS-backed apply flows, and automation-package boundaries. Historical plans from the broader repo may mention removed modules; treat those references as context, not current worktree truth.

## Documents

- `plan_docs/automation/directory_glossary.md` - target package glossary and ownership boundaries
- `plan_docs/automation/asset_placement.md` - where traces, playbooks, schemas, and docs belong
- `plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md` - refactor plan retained as design context
- `plan_docs/automation/2026-04-04-ariadne-common-language-issues.md` - open design issues for Ariadne common language (must resolve before Phase 2)
- `plan_docs/automation/superpowers_audit.md` - audit trail for removed exploratory docs (historical, not actionable in this worktree)

## Current rule

Keep planning scoped to browser automation. If a doc starts depending on deleted control-plane, rendering, or review-ui modules, rewrite it to the current worktree scope instead of preserving stale path references.
