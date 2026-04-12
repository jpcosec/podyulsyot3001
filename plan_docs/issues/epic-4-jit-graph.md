# EPIC 4: LangGraph JIT Orchestrator (The Controller)

**Explanation:** Replace the linear `session.py` loop with a declarative LangGraph `StateGraph` that manages the 4-level fallback cascade.

**Tasks:**
1.  **State Definition**: Implement the `AriadneState` with reducers for error accumulation and history tracking.
2.  **Topology Construction**: Build the 5-node graph: `Observe` -> `ExecuteDeterministic` -> `ApplyLocalHeuristics` -> `LLMRescueAgent` -> `HumanInTheLoop`.
3.  **Conditional Routing**: Implement the cost-optimized fallback edges (Deterministic -> Heuristics -> LLM -> HITL).
4.  **Micro-Batching**: Implement sequence look-ahead to group deterministic intents for Crawl4AI performance.

**Success Criteria:**
- Orchestration logic is purely declarative (the graph).
- The system can autonomously recover from UI changes using the fallback cascade.

**Depends on:** `epic-3-interface-taxonomy.md`
