# Conceptual Documentation Tree

This file defines the desired documentation tree for the repo.

Rule of thumb:

- `docs/` = current state, stable reference, operator truth
- `plan/` = planning, migration, ADRs, archived planning context
- heavy implementation docs = close to the code they explain

## Root tree

```text
PhD 2.0
├── README.md                        # repo entrypoint
├── docs/                            # current truth only
│   ├── index/                       # navigation only
│   ├── runtime/                     # current runnable backend/runtime behavior
│   ├── policy/                      # current enforceable policy/rules only
│   ├── reference/                   # stable current reference
│   ├── ui/                          # current UI/workbench/sandbox behavior
│   └── operations/                  # current operator playbooks
├── plan/                            # planning only
│   ├── adr/                         # architecture decisions
│   ├── runtime/                     # backend/runtime plans
│   ├── ui/                          # UI/workbench plans
│   ├── template/                    # plan templates and planning rules
│   └── archive/                     # archived plan snapshots worth keeping
└── code-local docs                  # heavy implementation docs near code
    ├── src/core/*/README.md
    ├── src/nodes/*/README.md
    └── apps/review-workbench/.../README.md
```

## What belongs in `docs/`

Only keep a document in `docs/` if it answers one of these:

1. what exists now
2. how it works now
3. how an operator uses it now
4. stable reference material needed across the repo

If a document is mostly future-looking, phased, speculative, migration-oriented, or historical, it does not belong in `docs/`.

## What belongs in `plan/`

Keep a document in `plan/` if it is:

- an implementation plan
- a migration plan
- an ADR
- an execution tracker
- a planning template
- archived planning context still worth keeping

Plans should be tree-shaped, include dependency trees, impact trees, testing, docs updates, changelog updates, and commit boundaries.

## What belongs near code

Move heavier implementation docs close to the code when they are mainly about:

- module internals
- maintenance notes
- subsystem-specific runtime contracts
- edge cases and implementation tradeoffs
- testing notes for a specific subsystem

Central docs should point to these instead of duplicating them.

Examples:

- `src/core/scraping/README.md`
- `src/core/io/README.md`
- `src/nodes/review_match/README.md`
- `src/nodes/render/README.md`
- `src/nodes/package/README.md`
- `apps/review-workbench/src/sandbox/README.md`

## Current-to-target mapping

### Current runtime truth set

- `README.md`
- `docs/graph/nodes_summary.md`
- `docs/graph/node_io_matrix.md`
- `docs/graph/match_review_cycle.md`
- `docs/reference/data_management_actual_state.md`
- `docs/operations/tool_interaction_and_known_issues.md`
- `docs/architecture/core_io_and_provenance_manager.md`

### Current docs that should gradually move/re-bucket

- runtime-oriented backend docs -> `docs/runtime/`
- enforceable business rules -> `docs/policy/`
- sandbox/workbench current behavior docs -> `docs/ui/`

### Current docs that should live in `plan/`

- target-state architecture docs
- migration docs
- phased UI implementation docs
- schema/spec docs that no longer mirror runtime

### Current docs that should be deleted when superseded

- old gap-tracking docs
- one-off implementation slices for already-completed work
- historical docs that add no planning or operational value

## Canonical ownership rule

- each concept should have one canonical home
- central docs summarize and link
- code-local docs hold heavy subsystem detail
- plans never masquerade as current runtime truth
- legacy docs should be moved, archived, or deleted, not left ambiguous

## Practical editing rule

Before creating or editing a doc, ask:

1. is this current truth, plan, or subsystem detail?
2. what is its canonical home in the tree?
3. can an existing central doc link to it instead of duplicating it?
4. if this becomes stale, should it be archived or deleted?
