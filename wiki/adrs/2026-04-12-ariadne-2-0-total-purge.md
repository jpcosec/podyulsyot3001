# ADR 2026-04-12: Ariadne 2.0 Total Purge & LangGraph Migration

## Status
Proposed

## Context
Ariadne 1.0 was built on a linear "tape-recorder" model (AOT compilation, array-based steps, while-loop orchestration). This architecture proved fragile against portal drift and created "leaky abstractions" where the domain core was tightly coupled to motor infrastructure and hardcoded heuristics.

## Decision
We will perform a total purge of the Ariadne 1.0 implementation. This includes:
1.  **Orchestration**: Deleting `session.py`, `discovery_session.py`, and `navigator.py`.
2.  **Contracts**: Deleting `motor_protocol.py`.
3.  **Heuristics**: Moving `job_normalization.py`, `form_analyzer.py`, and `danger_detection.py` to a `/legacy/` extraction area. Rules (magic strings) will be extracted to external Modes, and the files will then be deleted.
4.  **Tests & Scripts**: Deleting all unit tests and scripts associated with the 1.0 orchestration logic.

We will transition to **Ariadne 2.0**, a **Programmable Semantic Browser** based on:
- **LangGraph**: For dynamic, JIT, state-aware orchestration.
- **State Graphs**: Replacing linear paths with directed nodes and edges.
- **Nyxt Mode Pattern**: Injecting contextual URL-based rules.
- **Link Hinting (Set-of-Mark)**: For hallucination-free LLM navigation.

## Consequences
- **Positive**: High resilience to UI changes, clean SOLID boundaries, native HITL support, and cost-optimized fallback cascading.
- **Negative**: Temporary loss of functional apply flows until the 2.0 graph is implemented. Requires full re-migration of portal maps to the graph format.
