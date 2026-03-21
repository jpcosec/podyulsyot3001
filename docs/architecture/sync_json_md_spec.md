# sync_json_md Spec

## Status

This is an official future-facing spec.

### Implemented today

- Review markdown exists in the current runtime.
- Parsing and review-surface generation are still node-specific, not handled by one shared service.

### Future / target-state

- A shared `sync_json_md` service should own deterministic JSON <-> Markdown conversion with stale-hash safeguards.

## Intended location

- `src/core/tools/sync_json_md/`

## Planned API

1. `json_to_md(node, state_json_path, view_md_path, decision_md_path)`
2. `md_to_json(node, decision_md_path, decision_json_path, proposed_state_json_path)`

## Purpose

Provide deterministic conversion between canonical JSON artifacts and markdown review surfaces with stale-hash safeguards.

## Implementation gate

Do not mark this complete until reviewable nodes consume this service rather than writing review markdown manually.
