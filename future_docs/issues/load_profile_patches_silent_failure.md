# load_profile: propagate_profile_patches silently discards write failures

**Why deferred:** The fix requires changes to the `load_profile` node contract, which is a larger refactor; the immediate priority is the translate-node move and extract_bridge hardening.
**Last reviewed:** 2026-03-30

## Problem

`_propagate_patches_to_global_profile()` in `src/core/ai/match_skill/storage.py` catches `Exception`
and logs only a `warning` when profile patch writes fail. The caller (`load_profile` node) does not
inspect the return value for errors and continues with stale profile evidence. Patch feedback from a
HITL review round can be silently lost without any indication of failure in the run log.

## Why It Matters

- Profile evidence used for re-generation may not reflect reviewer corrections.
- The graph reports `status=running` even though user feedback was not applied.
- Log noise is low (only a WARNING), so operators are unlikely to notice.

## Proposed Direction

1. Change `_propagate_patches_to_global_profile()` to raise on write failure rather than warn.
2. In the `load_profile` node, catch the exception and return `status=failed` with a descriptive
   `error_state`.
3. Add a test that verifies `load_profile` sets `status=failed` when patch write raises.

## Linked TODOs

- `src/graph/nodes/load_profile.py` — `# TODO(future): propagate_profile_patches swallows write failures silently — see future_docs/issues/load_profile_patches_silent_failure.md`
