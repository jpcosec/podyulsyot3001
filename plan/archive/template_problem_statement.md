# Template Architecture Problem Statement

Related references:

- `plan/archive/structure_and_rationale.md`
- `docs/runtime/graph_flow.md`
- `docs/runtime/node_io_matrix.md`
- `docs/runtime/core_io_and_provenance.md`
- `plan/template/README.md`

## Purpose

This document defines the implementation problem we need to solve before writing the "smart template discipline".

The goal is to state the issue clearly, not to finalize the solution yet.

## Context

PhD 2.0 now has a clear execution taxonomy:

- **LLM-based**:
  - `extracting`
  - `matching`
  - `reviewing`
  - `redacting`
- **Non-LLM-based**:
  - `deterministic`
  - `non-deterministic` (bounded external variability)

We also have a strict graph with review gates and canonical artifact paths under:

- `data/jobs/<source>/<job_id>/nodes/<node>/...`

## Core issue

We need a code template system that is:

1. generic enough to avoid copy-paste drift,
2. strict enough to prevent wax-model behavior,
3. aligned with LangGraph execution patterns,
4. explicit about how node code interacts with:
   - job-specific persisted artifacts,
   - LangGraph state/checkpoint/runtime context.

Today, these aspects are documented separately, but we still need one coherent implementation discipline that maps taxonomy -> template -> concrete node behavior.

## Why this is a real problem

Without a disciplined template system, the rebuild risks repeating old failure modes:

1. **Style drift**: each node implements reader/logic/writer/gating differently.
2. **Boundary drift**: core and ai responsibilities blur over time.
3. **Wax-model regressions**: nodes pass structural tests but hide fallback semantics.
4. **State ambiguity**: unclear separation between graph state and persisted artifact state.
5. **Review inconsistency**: parser/routing semantics diverge by node.

## Design tension we must resolve

## 1) Inheritance vs composition

Question:

- Should templates be implemented as base classes with subclass overrides, or as function-first composition with shared helpers?

Risk if unresolved:

- too much inheritance can produce rigid class hierarchies,
- too little structure can recreate copy-paste boilerplate and inconsistency.

## 2) Graph state vs job artifact state

Question:

- What is the minimal LangGraph state that flows between nodes, and what must always be read/written from disk artifacts?

Risk if unresolved:

- hidden coupling between in-memory state and persisted truth,
- hard-to-debug resume behavior and checkpoint mismatch.

## 3) Taxonomy-to-template mapping

Question:

- How many template layers are needed from generic node -> taxonomy leaf -> concrete node?

Risk if unresolved:

- either over-abstraction (hard to use) or under-abstraction (inconsistent implementations).

## 4) LangGraph-native behavior

Question:

- What is the most "LangGraphesque" node contract for this project?

Risk if unresolved:

- node implementations that fight graph semantics (unclear routing, hidden side effects, weak interrupts).

## Scope of the next document

The upcoming "smart template discipline" document must provide:

1. a base node template,
2. one template per taxonomy leaf,
3. concrete guidance for each current pipeline node,
4. explicit class/composition guidance,
5. explicit state-contract guidance (graph state vs persisted artifacts),
6. review-gate/routing contract patterns,
7. anti-wax enforcement points.

## Non-goals for this problem statement

This document does **not**:

- define final class signatures,
- define exact Python module names for all templates,
- lock in inheritance as mandatory,
- replace stepwise implementation planning.

Those belong in the next design document.

## Success criteria for the next step

The next document is successful if, after reading it, we can implement any node category with:

1. predictable structure,
2. predictable routing behavior,
3. explicit I/O and state boundaries,
4. minimal boilerplate,
5. no ambiguity about where LLM behavior is allowed.
