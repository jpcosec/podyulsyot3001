# Nodes Module

Current role: node-local contracts and logic for pipeline stages.

## Current implemented prep-match path

1. `scrape`
2. `translate_if_needed`
3. `extract_understand`
4. `match`
5. `review_match`
6. `generate_documents`
7. `package` (prep terminal)

## Current status

- Several target review/generation nodes from the full architecture are not implemented yet.
- New nodes should follow existing contract/logic separation and fail-closed behavior.

## Testing

- Run node tests under `tests/nodes/`.
