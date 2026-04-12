# Ariadne 2.0 Implementation Index

Ariadne 2.0 has its **Architecture Core** implemented. We are now in the **Functional Restoration** phase to restore portal support, executors, and the CLI.

## Core Accomplishments (Architectural skeleton)
- [x] **Fitness Functions**: Enforced DIP, I/O isolation, and mode blindness.
- [x] **Graph Models**: Defined `AriadneMap`, `AriadneStateDefinition`, `AriadneEdge`.
- [x] **Mode Registry**: Built the Nyxt-inspired contextual mode system.
- [x] **Segregated Protocols**: Defined `Executor`, `Planner`, and `Capability` interfaces.
- [x] **StateGraph Controller**: Implemented the LangGraph JIT orchestrator.
- [x] **Link Hinting**: Implemented the "Set-of-Mark" DOM injection.
- [x] **JIT Translators**: Built atomic compilers for BrowserOS and Crawl4AI.
- [x] **Micro-Batching**: Implemented sequence grouping for C4A performance.
- [x] **Rescue Agent**: Built the direct MCP VLM rescue agent.

---

## Execution Queue (Functional Restoration)

### Phase 1: Portal Mode Implementations (Heuristics)
- [ ] **[Implement: LinkedIn Portal Mode Logic](gaps/implement-linkedin-portal-mode-logic.md)**
  - *Status*: Ready
  - *Expected*: Rules for LinkedIn-specific cleanup and recovery.
- [ ] **[Implement: StepStone Portal Mode Logic](gaps/implement-stepstone-portal-mode-logic.md)**
  - *Status*: Ready
  - *Expected*: German keyword rules and StepStone-specific recovery.

### Phase 2: Executor Restoration (The Hands)
- [ ] **[Rebuild: BrowserOS CLI Executor](unimplemented/rebuild-browseros-cli-executor.md)**
  - *Status*: Ready
  - *Expected*: JIT-compliant dumb worker for MCP calls.
- [ ] **[Rebuild: Crawl4AI JIT Executor](unimplemented/rebuild-crawl4ai-jit-executor.md)**
  - *Status*: Ready
  - *Expected*: JIT-compliant worker for C4A-Scripts.

### Phase 3: Map Migration (The Knowledge)
- [ ] **[Migrate: Portal Maps to AriadneMap Graph](unimplemented/migrate-portal-maps-to-graph.md)**
  - *Status*: Ready (Architecture-ready)
  - *Expected*: `easy_apply.json` graphs for StepStone and LinkedIn.

### Phase 4: CLI & Entrypoint (The Interface)
- [ ] **[Rebuild: CLI Entrypoint for Ariadne 2.0](unimplemented/rebuild-cli-entrypoint.md)**
  - *Status*: Ready
  - *Expected*: Functional `python -m src.automation.main apply` invoking the 2.0 graph.

---

## QA & Validation
Portal-specific bugs and validation tracking are managed in [QA_BACKLOG.md](../../QA_BACKLOG.md).
