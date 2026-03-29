# Pipeline Unification Follow-Ups

**Why deferred:** The pipeline MVP is wired end-to-end, but a few contract and migration gaps are still being carried as implementation debt while the current orchestration path stabilizes.
**Last reviewed:** 2026-03-29

## Problem / Motivation

The current pipeline direction is mostly settled, but one migration gap still remains in the active implementation:

- Standalone legacy module flows still coexist with the schema-v0 pipeline in a few places, especially around the old `output/match_skill` storage root and review tooling.

These are not Stage 7 hardening items. They are follow-up architecture and contract cleanup required to finish the non-future parts of pipeline unification cleanly.

## Proposed Direction

- Complete the cutover from legacy standalone artifact roots to the schema-v0 `data/jobs/...` contract.
- Keep the standalone review and module CLIs working, but decide explicitly whether they remain legacy-compatible wrappers or move fully onto the new data-plane contract.

## Linked TODOs

- `src/cli/main.py` — align the unified review flow with the schema-v0 runtime roots if review should stop depending on `output/match_skill`
- `src/ai/match_skill/main.py` — decide whether the standalone match CLI remains legacy-rooted or gains a schema-v0 mode
- `src/ai/match_skill/storage.py` — decide whether the default root should remain `output/match_skill` for compatibility or move to `data/jobs`
