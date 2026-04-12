# Ariadne 2.0 Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

## Working rule for every issue

Once an issue is solved, the next step is always:

 1. Check whether any existing test is no longer valid and delete it if needed.
 2. Add new tests where necessary.
 3. Run the relevant tests.
 4. Update changelog.md.
 5. Delete the solved issue from both this index and the corresponding file in plan_docs/issues/.
 6. Make a commit that clearly states what was fixed, making sure all required files are staged.

## Priority roadmap

### Phase 1 — Execution & State Integrity (Hotfixes)

 1. plan_docs/issues/gaps/implement-mission-driven-pathfinding.md
    • [Prevents wrong turns in the graph]

 2. plan_docs/issues/gaps/atomic-micro-batching-with-failure-index.md
    • [Guarantees DOM state consistency]

 3. plan_docs/issues/gaps/state-patch-leak-prevention.md
    • [Avoids "ghost clicks" from stale patches]

### Phase 2 — Performance & UI Polish

 4. plan_docs/issues/gaps/async-mode-config-loading.md
    • [Removes blocking I/O from the hot loop]

 5. plan_docs/issues/gaps/robust-hint-anchoring.md
    • [Ensures LLM hints work in scrollable containers]

### Phase 3 — Intelligence & Data Polish

 6. plan_docs/issues/gaps/implement-llm-fallback-in-default-mode.md
    • [Critical for unmapped portal support]

 7. plan_docs/issues/gaps/restore-danger-detection-capability.md
    • [Re-integrates CAPTCHA and security block detection]

### Phase 4 — Scraper & Discovery

 8. plan_docs/issues/gaps/restore-discovery-graph-mission.md
    • [Restores the 'scrape' command using the Ariadne 2.0 graph]

### Phase 5 — The Lifecycle (Learning)

 9. plan_docs/issues/gaps/implement-persistent-sqlite-checkpointer.md
    • [Enables production-grade HITL and session recovery]

 10. plan_docs/issues/gaps/implement-graph-recorder-capability.md
    • [Captures JIT transitions for map promotion]

 11. plan_docs/issues/gaps/implement-promotion-engine.md
    • [Converts recordings into canonical AriadneMap candidates]


## Dependency summary

• plan_docs/issues/gaps/restore-discovery-graph-mission.md  ->  plan_docs/issues/gaps/implement-mission-driven-pathfinding.md
• plan_docs/issues/gaps/implement-graph-recorder-capability.md  ->  plan_docs/issues/gaps/implement-persistent-sqlite-checkpointer.md
• plan_docs/issues/gaps/implement-promotion-engine.md  ->  plan_docs/issues/gaps/implement-graph-recorder-capability.md

## Parallelization map

Phase 1  [1][2][3]       ← [Hotfixes]
Phase 2  [4][5]          ← [Polish]
Phase 3  [6][7][8]       ← [Functional]
Phase 4  [9][10][11]     ← [Lifecycle]
