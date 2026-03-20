# review_match Node

This node is the current active semantic review gate in the runnable prep-match flow.

## Responsibilities

- ensure `nodes/match/review/decision.md` exists
- validate `source_state_hash`
- parse checkbox decisions deterministically
- write `decision.json` and round-local `feedback.json`
- route to `approve`, `request_regeneration`, or `reject`

## Important runtime notes

- current operator workflow edits `decision.md`, not JSON directly
- regeneration feedback can include `PATCH_EVIDENCE:` notes
- stale or ambiguous review input fails closed

## Central references

- `docs/runtime/match_review_cycle.md`
- `docs/runtime/data_management.md`
- `docs/operations/tool_interaction_and_known_issues.md`
