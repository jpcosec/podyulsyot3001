# Automation Planning Docs

This folder is the planning-doc home for the browser automation worktree.

## Status

The Phase 1 migration (2026-04-06) is **complete**. `src/scraper/` and `src/apply/` have been removed and replaced by `src/automation/`. The implemented layout is documented in `src/automation/README.md`.

## Documents

### Active design references (Ariadne Phase 2 and beyond)

- `plan_docs/automation/2026-04-04-ariadne-common-language-issues.md` — open design issues for Ariadne common language (must resolve before Phase 2)

### Completed migration context (retained for design history)

- `plan_docs/automation/directory_glossary.md` — pre-migration target directory glossary and ownership boundaries
- `plan_docs/automation/asset_placement.md` — pre-migration asset classification decisions (all resolved)
- `plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md` — original refactor plan (predates Ariadne portal schema design)
- `plan_docs/automation/superpowers_audit.md` — audit trail for removed exploratory docs (historical)

## Current rule

Keep planning scoped to browser automation. The Phase 2 scope (Ariadne storage, recorder, replayer, promotion, BrowserOS agent path, routing.py) is tracked in `plan_docs/automation/2026-04-04-ariadne-common-language-issues.md` and the sibling `plan_docs/ariadne/` folder.
