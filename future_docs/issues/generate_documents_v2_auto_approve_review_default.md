# generate_documents_v2: `auto_approve_review` defaults to `True`, silently bypassing HITL

**Why deferred:** Changing the default is a breaking change for any caller that currently relies on the auto-approve behaviour (e.g. pipeline integration tests, CLI batch runs). Requires auditing all call sites before flipping.
**Last reviewed:** 2026-03-31

## Problem

In `src/core/ai/generate_documents_v2/graph.py`, both the review node function (line 320) and the routing function (line 393) use:

```python
state.get("auto_approve_review", True)
```

The default `True` means that unless a caller explicitly sets `auto_approve_review=False` in the initial state, all three HITL review interrupts (`review_match`, `review_blueprint`, `review_bundle`) are skipped and the graph auto-approves every stage.

The `interrupt_before` compilation breakpoints are still set up correctly, so the graph *looks* like it has HITL from the outside — but the review node immediately routes past the interrupt without reading any patches.

## Why It Matters

- A caller who instantiates the graph without setting `auto_approve_review=False` gets silent auto-approval across all review stages.
- No warning or log is emitted when auto-approve fires.
- The risk increases when the graph is invoked from the pipeline node (`src/graph/nodes/generate_documents.py`), which currently passes no `auto_approve_review` key, making auto-approve the production default.

## Proposed Direction

Option A (preferred): Change the default to `False` in both usages. Update any callers that relied on the old default to explicitly pass `auto_approve_review=True` if they want batch mode.

Option B: Remove `auto_approve_review` from state entirely. Control batch vs HITL mode at graph compilation time by compiling without `interrupt_before` for batch runs, as LangGraph intends.

## Linked TODOs

- `src/core/ai/generate_documents_v2/graph.py:320` — `# TODO(future): default True silently bypasses HITL — see future_docs/issues/generate_documents_v2_auto_approve_review_default.md`
- `src/core/ai/generate_documents_v2/graph.py:393` — same
