# Graph State Contract

## Status

This is a mixed-status reference.

### Implemented today

- The current runtime shape lives in `src/core/graph/state.py`.
- The runnable prep-match flow still carries some transient semantic payloads in state.

### Future / target-state

- `GraphState` should converge to a control-plane ledger carrying routing data and lightweight refs only.
- Heavy semantic payloads should live on disk artifacts instead of state.

## Current rule of thumb

- Use `src/core/graph/state.py` for what actually exists.
- Use this doc for the intended boundary.

## Target boundary

`GraphState` should own:

1. run identity
2. execution status
3. current node
4. review decision signals
5. error context
6. lightweight artifact references

It should not become a container for large reviewable payloads.
