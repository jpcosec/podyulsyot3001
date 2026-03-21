# Artifact Schemas

## Status

This is a mixed-status reference.

### Implemented today

- Current artifact behavior for the runnable prep-match flow is documented in `docs/runtime/data_management.md` and `docs/runtime/node_io_matrix.md`.
- The implemented flow covers artifacts for `scrape`, `translate_if_needed`, `extract_understand`, `match`, `review_match`, `generate_documents`, `render`, and `package`.

### Future / target-state

- The full multi-review-chain artifact set remains target-state only.
- Shared review-surface generation via a central `sync_json_md` service is future work.

## Use this file for

- stable naming conventions
- target-state artifact expectations
- separating current implemented artifacts from future ones

## Current implemented artifact groups

1. Scrape artifacts under `nodes/scrape/`.
2. Translation approved state under `nodes/translate_if_needed/approved/`.
3. Extraction approved state under `nodes/extract_understand/approved/`.
4. Match approved state plus review files under `nodes/match/`.
5. Review parser outputs under `nodes/match/review/`.
6. Document generation outputs under `nodes/generate_documents/`.
7. Render outputs under `nodes/render/`.
8. Final packaged deliverables under `final/` and `nodes/package/`.

## Future artifact groups

- `build_application_context`
- `review_application_context`
- `generate_motivation_letter`
- `review_motivation_letter`
- `tailor_cv`
- `review_cv`
- `draft_email`
- `review_email`

## Rule

If this file and current runtime docs disagree, trust the current runtime docs.
