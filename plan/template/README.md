# Node Folder Templates (Plan View)

This plan-level template guide is aligned with the canonical architecture discipline in:

- `docs/templates/node_template_discipline.md`
- `docs/architecture/core_io_and_provenance_manager.md`

## Canonical node package shape

All nodes must use:

```text
src/<domain>/nodes/<node_name>/
  __init__.py
  contract.py
  logic.py
  node.py
  prompt/          # LLM nodes only
    system.md
```

Where:

- `<domain>` is `core` for non-LLM nodes and `ai` for LLM nodes.
- per-node `reader.py` and `writer.py` are not used.
- I/O is centralized in `src/core/io/` through `WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, and `ProvenanceService`.

## Responsibility split

- `contract.py`: strict schemas for node inputs/outputs.
- `logic.py`: pure behavior (no filesystem I/O).
- `node.py`: orchestration (`read -> logic -> write -> route`).
- `prompt/`: node-local prompt assets for LLM nodes.

## Quick taxonomy mapping

- Non-LLM deterministic (`NLLM-D`): reproducible transforms.
- Non-LLM bounded-nondeterministic (`NLLM-ND`): external variability with strict retries.
- LLM extracting: JSON distillation/consolidation.
- LLM matching: requirement/evidence mapping + review surfaces.
- LLM redacting: narrative draft + state for review.
- Reviewing parser nodes (non-LLM): deterministic decision parse and routing.

## Anti-wax guardrails

1. No fake success output in retry handlers.
2. No payload bloat in GraphState.
3. No manual path construction outside `WorkspaceManager`.
4. No downstream consumption from `proposed/` when `approved/` is required.
