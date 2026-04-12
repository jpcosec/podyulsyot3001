# Ariadne 2.0: Master Implementation Index

This index tracks the 6 core Epics required to transition Ariadne to a **"Programmable Semantic Browser"** based on LangGraph.

## Execution Queue (Priority Order)

### [EPIC 0: Demolition & Recycling (Cleanup)](epic-0-cleanup.md)
- **Status**: Ready
- **Scope**: Isolate legacy code, purge contradictory specs, and setup QA Backlog.
- **Depends on**: none

### [EPIC 1: Architectural Fitness Functions (The Armor)](epic-1-fitness-functions.md)
- **Status**: Locked (Blocked by Epic 0)
- **Scope**: Implement `pytest-archon` and `pyfakefs` guardrails to enforce design boundaries.
- **Depends on**: Epic 0

### [EPIC 2: Data Layer & Portal Modes (The Stupid Brain)](epic-2-data-layer-modes.md)
- **Status**: Blocked
- **Scope**: Migrate to State Graphs and implement the Contextual Mode Pattern.
- **Depends on**: Epic 1

### [EPIC 3: Interface Taxonomy & Capabilities (The Segregation)](epic-3-interface-taxonomy.md)
- **Status**: Blocked
- **Scope**: Refactor Motor protocols into primitive JIT interfaces and implement Hinting.
- **Depends on**: Epic 2

### [EPIC 4: LangGraph JIT Orchestrator (The Controller)](epic-4-jit-graph.md)
- **Status**: Blocked
- **Scope**: Implement the 5-node StateGraph topology and JIT translation loop.
- **Depends on**: Epic 3

### [EPIC 5: LangGraph MCP Rescue Agent (The Planner)](epic-5-mcp-rescue-agent.md)
- **Status**: Blocked
- **Scope**: Implement the Level 3 LLM Rescue Agent with direct MCP tools.
- **Depends on**: Epic 4

---

## Working Rules
Once an issue is solved:
1.  Run the **Fitness Functions** to ensure no architectural drift.
2.  Update `changelog.md`.
3.  Delete the solved issue from this index and its file.
4.  Commit the change.

## Bug & Validation Tracking
All portal-specific bugs and dry-run validation tasks are tracked in [QA_BACKLOG.md](../../QA_BACKLOG.md).
