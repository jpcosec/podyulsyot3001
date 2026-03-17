# sync_json_md Spec

Status: planned, not implemented in current codebase.

## Intended location

- `src/core/tools/sync_json_md/`

## Planned API

1. `json_to_md(node, state_json_path, view_md_path, decision_md_path)`
2. `md_to_json(node, decision_md_path, decision_json_path, proposed_state_json_path)`

## Purpose

Provide deterministic conversion between canonical JSON artifacts and markdown review surfaces with stale-hash safeguards.

## Implementation gate

Do not mark complete until reviewable nodes consume this service rather than writing review markdown manually.
