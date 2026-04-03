# generate_documents_v2: Profile Feedback Updater Is Still a Placeholder

**Why deferred:** Persisting post-review learning back into the profile safely needs a clear approval model, write contract, and conflict policy.
**Last reviewed:** 2026-04-03

## Problem / Motivation

The design docs described a feedback loop where review-time insights improve future runs. In the current code, the profile updater in `src/core/ai/generate_documents_v2/graph.py` is explicitly a no-op.

```python
logger.info("%s Profile updater: (no-op in v2 prototype)", LogTag.OK)
```

So the pipeline does not currently learn from:

- emergent evidence added during review
- blueprint corrections
- style adjustments the operator prefers

## Proposed Direction

- Define a typed patch contract for profile updates.
- Separate temporary per-application edits from durable profile learning.
- Require explicit approval before writing persistent profile changes.

## Related code

- `src/core/ai/generate_documents_v2/graph.py`
- `src/core/ai/generate_documents_v2/contracts/hitl.py`
