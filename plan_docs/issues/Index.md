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

### Phase 1 — Intelligence & Data Polish

 1. plan_docs/issues/gaps/implement-llm-fallback-in-default-mode.md
    • [Critical for unmapped portal support]

 2. plan_docs/issues/gaps/implement-mission-driven-pathfinding.md
    • [Prevents the orchestrator from taking wrong transitions]

 3. plan_docs/issues/gaps/restore-danger-detection-capability.md
    • [Re-integrates CAPTCHA and security block detection]

### Phase 2 — Infrastructure & Persistence

 4. plan_docs/issues/gaps/implement-persistent-sqlite-checkpointer.md
    • [Enables production-grade HITL and session recovery]

 5. plan_docs/issues/gaps/implement-graph-recorder-capability.md
    • [Captures JIT transitions for map promotion]

### Phase 3 — Scraper & Discovery

 6. plan_docs/issues/gaps/restore-discovery-graph-mission.md
    • [Restores the 'scrape' command using the Ariadne 2.0 graph]

### Phase 4 — The Lifecycle (Learning)

 7. plan_docs/issues/gaps/implement-promotion-engine.md
    • [Converts recordings into canonical AriadneMap candidates]

## Dependency summary

• plan_docs/issues/gaps/implement-graph-recorder-capability.md  ->  plan_docs/issues/gaps/implement-persistent-sqlite-checkpointer.md
• plan_docs/issues/gaps/restore-discovery-graph-mission.md  ->  plan_docs/issues/gaps/implement-mission-driven-pathfinding.md
• plan_docs/issues/gaps/implement-promotion-engine.md  ->  plan_docs/issues/gaps/implement-graph-recorder-capability.md

## Parallelization map

Phase 1  [1][2][3]       ← [Polish]
Phase 2  [4][5]          ← [Infrastructure]
Phase 3  [6][7]          ← [Functional]
