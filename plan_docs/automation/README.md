# Automation Planning Docs

This folder is the planning-doc home for the unified automation refactor.

It exists before any runtime move so the target structure, ownership boundaries,
and asset-placement rules are explicit before code changes begin.

## Documents

- `plan_docs/automation/directory_glossary.md` - target package glossary and ownership boundaries
- `plan_docs/automation/asset_placement.md` - where traces, playbooks, schemas, and docs belong
- `docs/repo_maps/current_repo_scrape_apply_browseros_ariadne_map.md` - current repo inventory
- `docs/repo_maps/worktree_feat_apply_module_map.md` - worktree inventory
- `plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md` - approved refactor plan

## Current rule

No runtime move should begin until the glossary and asset-placement documents are
approved and used as the migration reference.
