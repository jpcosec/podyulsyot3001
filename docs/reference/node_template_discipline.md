# Node Template Discipline

## Status

This is a mixed-status reference.

### Implemented today

- Nodes in `src/nodes/` already follow a recognizable package pattern with `contract.py`, `logic.py`, and prompt assets for LLM nodes.
- Some newer runtime slices use `src/core/io/`, while older ones still do inline path I/O.

### Future / target-state

- All nodes should use a consistent shared I/O layer.
- Orchestration, review-surface generation, and provenance patterns should become uniform.

## Current practical rule

- Follow existing node-local contracts and current runtime behavior.
- Prefer the shared I/O layer when implementing new work.

## Target discipline

1. consistent package shape
2. deterministic fail-closed behavior
3. minimal `GraphState`
4. data-plane artifacts as the semantic source of truth
5. uniform review and provenance handling
