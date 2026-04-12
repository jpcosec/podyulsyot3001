# Ariadne 2.0 Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

All issue-fixing work must stay aligned with the rest of plan_docs/ and wiki/, with special care for wiki/standards/ so implementation, tests, and documentation remain consistent with the project's rules.

## Working rule for every issue

Once an issue is solved, the next step is always:

 1. Check whether any existing test is no longer valid and delete it if needed.
 2. Add new tests where necessary.
 3. Run the relevant tests.
 4. Update changelog.md.
 5. Delete the solved issue from both this index and the corresponding file in plan_docs/issues/.
 6. Make a commit that clearly states what was fixed, making sure all required files are staged.

## Priority roadmap

### Phase 1 — Intelligence & Logic Polish

 1. plan_docs/issues/gaps/implement-llm-fallback-in-default-mode.md
    • [Critical for unmapped portal support]

### Phase 2 — Infrastructure & Persistence

 2. plan_docs/issues/gaps/implement-persistent-sqlite-checkpointer.md
    • [Enables production-grade HITL and session recovery]

### Phase 3 — The Lifecycle (Learning)

 3. plan_docs/issues/gaps/implement-graph-recorder-capability.md
    • [Captures JIT transitions for map promotion]

 4. plan_docs/issues/gaps/implement-promotion-engine.md
    • [Converts recordings into canonical AriadneMap candidates]

## Dependency summary

• plan_docs/issues/gaps/implement-graph-recorder-capability.md  ->  plan_docs/issues/gaps/implement-persistent-sqlite-checkpointer.md
• plan_docs/issues/gaps/implement-promotion-engine.md  ->  plan_docs/issues/gaps/implement-graph-recorder-capability.md

## Parallelization map

Phase 1  [1]          ← [Intelligence] Phase 2     [2]          ← [Persistence] Phase 3     [3][4]       ← [Learning]
