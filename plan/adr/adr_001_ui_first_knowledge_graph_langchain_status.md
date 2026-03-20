# ADR-001 Status in Current Codebase

This file records the current implementation status of ADR-001 in `docs/`.

Planning details and future-state sequencing are maintained in:

- `plan/adr/adr_001_ui_first_knowledge_graph_langchain.md`
- `plan/adr_001_execution_tracker.md`

## Current implementation snapshot

Implemented today:

- React review workbench scaffold under `apps/review-workbench/`
- Filesystem-backed review API under `src/interfaces/api/`
- Read-only payload routes for timeline and View 1/2/3
- Neo4j health/bootstrap endpoints and CLI scaffolding

Not implemented today:

1. Neo4j as primary data plane for review payloads
2. UI editing/comment workflow across views
3. LangChain migration (`LLMRuntime`/`PromptManager` replacement)
4. Full target graph path through render/package gates

For exact phase-by-phase fulfillment levels and blockers, see `plan/adr_001_execution_tracker.md`.
