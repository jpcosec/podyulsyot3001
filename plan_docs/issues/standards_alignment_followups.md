# Standards Alignment Follow-Ups

**Why deferred:** The pipeline MVP shipped by prioritizing end-to-end wiring, but several files currently diverge from the repository's code and documentation standards and should be normalized in a follow-up pass.
**Last reviewed:** 2026-03-29

## Problem / Motivation

The current implementation is much closer to the standards now. The main remaining mismatch is strategic rather than structural:

- The unified CLI and some standalone module entrypoints still straddle two runtime contracts (`data/jobs` for schema-v0 orchestration and `output/match_skill` for legacy standalone compatibility). That keeps the codebase functional, but it is not the cleanest final layer boundary.

These do not block the current MVP path, but they should be tracked explicitly so the repo does not normalize drift from its own standards.

## Proposed Direction

- Decide which standalone interfaces remain compatibility wrappers and which should become schema-v0 native entrypoints.
- Once that decision is made, align the remaining READMEs and CLI examples to one explicit runtime story.

## Linked TODOs

- `src/cli/main.py` — decide whether the unified CLI should continue exposing legacy review storage roots or route entirely through schema-v0 runtime abstractions
- `src/ai/match_skill/README.md` — keep the README aligned with whichever standalone-vs-schema-v0 decision is taken for match/review flows
- `src/review_ui/README.md` — keep the runtime/storage examples aligned with the final review storage decision
