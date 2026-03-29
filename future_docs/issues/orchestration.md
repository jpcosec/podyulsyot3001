# Orchestration

**Why deferred:** The pipeline currently has no top-level orchestrator; modules are invoked independently and the boundary between `match_skill` and `generate_documents` is inconsistent across docs and code.
**Last reviewed:** 2026-03-29

## Problem / Motivation

Two concrete problems:

1. **`generate_documents` identity confusion.** The `match_skill_product_guide.md` describes `generate_documents` as the final node *inside* the match_skill graph. In reality, `src/ai/generate_documents/` is a standalone LangGraph module with its own graph, contracts, storage, and main. The two descriptions are contradictory. It is unclear which is the intended design — an embedded node or a separate graph called after approval.

2. **No end-to-end pipeline entry point.** The full flow (scrape → translate → match → generate → render) has no single orchestrator. `PIPELINE_MAPPING.md` documents the mapping from the old pipeline but does not define how the modules are composed in practice. Users must manually chain CLI commands or API calls. It is not clear whether the intended architecture is a unified LangGraph graph, a shell script, or an API caller.

## Proposed Direction

- Decide: is `generate_documents` a node inside the match_skill graph, or a separate graph invoked after approval? Update `match_skill_product_guide.md` to match the decision.
- Define the top-level pipeline composition strategy (unified graph vs. sequential CLI vs. API orchestration).
- If a unified graph is desired, design the top-level `StateGraph` that chains `match_skill` → `generate_documents` → `render`.
- Update `PIPELINE_MAPPING.md` from a historical mapping to a forward-looking architecture diagram.

## Linked TODOs

- `src/ai/generate_documents/graph.py` — `# TODO(future): clarify whether this graph is standalone or embedded in match_skill — see future_docs/issues/orchestration.md`
- `src/PIPELINE_MAPPING.md` — `# TODO(future): replace old→new mapping with forward-looking pipeline composition spec — see future_docs/issues/orchestration.md`
