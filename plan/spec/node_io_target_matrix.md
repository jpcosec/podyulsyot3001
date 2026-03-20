# Node I/O Matrix (Target State Spec)

This document contains the forward-looking node I/O contract for the full graph.

It is intentionally in `plan/spec/` because parts are not implemented yet.

## Target path

`scrape -> translate_if_needed -> extract_understand -> match -> review_match -> build_application_context -> review_application_context -> generate_motivation_letter -> review_motivation_letter -> tailor_cv -> review_cv -> draft_email -> review_email -> render -> package`

## Review routing (target)

- `approve` -> continue
- `request_regeneration` -> return to generator node
- `reject` -> terminate run

## Required properties

1. All generator outputs must be persisted under `nodes/<node>/proposed/`.
2. All review decisions must be persisted under `nodes/<node>/review/decision.{md,json}` with stale-hash safety.
3. Downstream nodes may consume only `approved/` artifacts.
4. Provenance metadata is required for approved outputs in reviewable paths.
5. No silent fallback-to-success behavior is allowed.

## Detailed source

The historical full target table is preserved in git history from pre-protocol `docs/runtime/node_io_matrix.md` revisions.

Use this file as the planning anchor and expand row-by-row only when implementation work is actively scheduled.
