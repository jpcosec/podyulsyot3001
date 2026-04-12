# Ariadne 2.0 Implementation Index

Ariadne 2.0 has its **Architecture Core** and **Skeleton** implemented. We are now in the **Logic Implementation** phase to turn stubs into functional code.

## Core Accomplishments (Skeleton)
- [x] **Fitness Functions**: DIP/Isolation guardrails passing.
- [x] **Graph Models**: 2.0 models defined.
- [x] **Mode Registry**: Contextual mode classes created.
- [x] **StateGraph Topology**: 5-node graph structure compiled.
- [x] **JIT Translators**: Atomic intent compilers implemented.

---

## Execution Queue (Logic Implementation)

### Phase 1: Closing the Loop (Node Logic)
- [ ] **[Implement: Observe Node Logic](gaps/implement-observe-node-logic.md)**
  - *Status*: Ready
  - *Scope*: Replace stub in `orchestrator.py` with actual calls to fetch URL, DOM, and Screenshot.
- [ ] **[Implement: Deterministic Dispatch Logic](gaps/implement-deterministic-dispatch-logic.md)**
  - *Status*: Ready
  - *Scope*: Connect `execute_deterministic_node` to `MotorRegistry` and handle `ExecutionResult`.
- [ ] **[Implement: Local Heuristics Logic](gaps/implement-local-heuristics-logic.md)**
  - *Status*: Ready
  - *Scope*: Implement the patching rules in `ApplyLocalHeuristicsNode` using `portal_mode`.

### Phase 2: Executor De-Mocking (The Hands)
- [ ] **[Implement: Crawl4AI Live Execution](gaps/implement-crawl4ai-live-execution.md)**
  - *Status*: Ready
  - *Scope*: Replace mocks in `Crawl4AIExecutor` with `AsyncWebCrawler.arun()` calls.
- [ ] **[Verify: BrowserOS MCP Parameters](gaps/verify-browseros-mcp-parameters.md)**
  - *Status*: Ready
  - *Scope*: Ensure `BrowserOSCliExecutor` tool calls match the live port 9000 schema exactly.

### Phase 3: CLI & Lifecycle
- [ ] **[Refine: CLI Apply Lifecycle](gaps/refine-cli-apply-lifecycle.md)**
  - *Status*: Ready
  - *Scope*: Handle streaming updates, state persistence, and end-to-end success/failure reporting.

---

## QA & Validation
Portal-specific bugs and map validation are managed in [QA_BACKLOG.md](../../QA_BACKLOG.md).
