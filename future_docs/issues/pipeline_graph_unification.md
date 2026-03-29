# Pipeline Graph Unification — Match Skill as Native Subgraph

**Why deferred:** Current pipeline is functional. Restructuring requires rethinking the graph topology and resolving the Command-based routing limitation without breaking HITL checkpointing.
**Last reviewed:** 2026-03-29

## Problem / Motivation

Two related structural problems exist in the current pipeline:

### 1. Match skill is an opaque wrapper node, not a subgraph

In `src/graph/__init__.py`, `match_skill` is registered as a single opaque node via `make_match_skill_node`. Internally, the node builds and `ainvoke`s a full `MatchSkillState` graph, but this is invisible to the parent pipeline graph. LangGraph Studio shows it as one black box. The internal loop (`load_match_inputs → run_match_llm → persist_match_round → human_review_node → apply_review_decision → …`) cannot be visualized or interacted with from the pipeline view.

The correct approach is to compose `match_skill` as a native LangGraph subgraph using `workflow.add_node("match_skill", subgraph)`, which makes the entire inner topology visible in Studio and checkpointed within the same thread.

### 2. Command-based routing causes unconnected nodes in Studio

In `src/ai/match_skill/graph.py`, `apply_review_decision` routes using `Command(goto=...)` at runtime. LangGraph Studio builds the visual topology statically and cannot infer `Command`-based destinations. As a result, `prepare_regeneration_context` and `generate_documents` appear as orphan/unconnected nodes in the Studio canvas even though they are reachable at runtime.

The fix is to declare routing via `add_conditional_edges` so the topology is statically known, even if the routing function reads state at runtime.

## Proposed Direction

Unify the pipeline into a single LangGraph graph where `match_skill` is a native subgraph:

1. Refactor `src/ai/match_skill/graph.py` to expose `build_match_skill_graph` as a compiled subgraph compatible with `workflow.add_node`.
2. Replace the `Command`-based routing in `apply_review_decision` with conditional edges declared via `add_conditional_edges`, keeping routing logic in a normal routing function.
3. Remove the opaque wrapper node `src/graph/nodes/match_skill.py` and directly embed the subgraph in `src/graph/__init__.py`.
4. Ensure the HITL breakpoint (`interrupt_before=["human_review_node"]`) is preserved through subgraph checkpointing.
5. Update `langgraph.json` if the standalone `match_skill` graph entry is still needed for direct inspection.

The result should be a single pipeline graph where all nodes and edges — including the inner match skill loop — are statically visible in Studio with no orphan nodes.

## Linked TODOs

- `src/graph/__init__.py` — `# TODO(future): embed match_skill as native subgraph instead of opaque wrapper node`
- `src/graph/nodes/match_skill.py` — `# TODO(future): remove wrapper — match_skill should be a subgraph in the pipeline graph`
- `src/ai/match_skill/graph.py` — `# TODO(future): replace Command-based routing with add_conditional_edges for static Studio visibility`
