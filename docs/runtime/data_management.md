# Data Management and Semantics (Actual Codebase State)

Related references:

- `src/core/graph/state.py`
- `src/graph.py`
- `src/cli/run_prep_match.py`
- `src/nodes/review_match/logic.py`
- `src/nodes/generate_documents/logic.py`
- `src/nodes/render/logic.py`
- `src/nodes/package/logic.py`
- `src/core/io/`

## Purpose

This document describes how data is actually stored, moved, and interpreted in the current codebase.

It is intentionally implementation-first. Where it differs from target architecture docs, this file records current behavior without normalization.

## Authority scope

- Canonical owner for current runtime data behavior.
- Not the owner of final or target schema design.

## Current execution surface (implemented)

The executable graph helper in daily use is the prep-match flow:

1. `scrape`
2. `translate_if_needed`
3. `extract_understand`
4. `match`
5. `review_match`
6. `generate_documents`
7. `render`
8. `package`

Implemented by:

- `src/graph.py` via `build_prep_match_node_registry()`, `create_prep_match_app()`, `run_prep_match()`
- `src/cli/run_prep_match.py` for operator execution and resume

Current review routing:

- `approve` -> `generate_documents`
- `request_regeneration` -> `match`
- `reject` -> end

## Storage roots and ownership

### Job workspace root

- Root: `data/jobs/<source>/<job_id>/`

### Profile base snapshot

- Default profile snapshot used by `generate_documents` fallback:
  - `data/reference_data/profile/base_profile/profile_base_data.json`

### Checkpoints

- Default runtime checkpoint path:
  - `data/jobs/<source>/<job_id>/graph/checkpoint.sqlite`

## Control-plane data (GraphState) in current code

`GraphState` is defined in `src/core/graph/state.py`.

Current state includes both routing metadata and transient payload fields:

- Routing/identity: `source`, `job_id`, `run_id`, `source_url`, `current_node`, `status`, `review_decision`, `pending_gate`, `error_state`, `artifact_refs`
- Transient payloads: `ingested_data`, `extracted_data`, `matched_data`, `my_profile_evidence`, `last_decision`, `active_feedback`

Meaning:

- the repo is moving toward a control-plane-only state model,
- but current runtime still carries semantic payloads in memory between nodes.

## Data-plane artifacts currently written and consumed

All paths below are relative to `data/jobs/<source>/<job_id>/`.

| Path | Producer in current codebase | Meaning / usage |
| --- | --- | --- |
| `raw/raw.html` | scrape subsystem / legacy backfills | Raw fetched HTML source for audit/debug. |
| `raw/source_text.md` | scrape subsystem | Human-readable extracted source text. |
| `raw/language_check.json` | translation or legacy scrape utilities | Language detection/translation diagnostics when available. |
| `nodes/scrape/input/fetch_metadata.json` | `src/core/scraping/service.py` | Fetch mode, source URL, and fetch policy metadata. |
| `nodes/scrape/input/raw_snapshot.json` | `src/core/scraping/service.py` | Raw fetch snapshot metadata/content envelope. |
| `nodes/scrape/input/source_extraction.json` | `src/core/scraping/service.py` | Extracted text/structured scrape details before canonical normalization. |
| `nodes/scrape/input/listing_crawl.json` | `src/cli/run_scrape_probe.py` listing mode | Listing crawl results and discovered detail URLs for operator inspection. |
| `nodes/scrape/approved/canonical_scrape.json` | `src/core/scraping/service.py` | Canonical scrape envelope used by downstream scrape node compatibility logic. |
| `nodes/translate_if_needed/approved/state.json` | `src/nodes/translate_if_needed/logic.py` | Scrape payload plus translation flags (`translated`, `translated_to`). |
| `nodes/extract_understand/approved/state.json` | `src/nodes/extract_understand/logic.py` | Structured job understanding (`requirements`, `constraints`, `risk_areas`). |
| `nodes/match/approved/state.json` | `src/nodes/match/logic.py` | Canonical persisted match envelope (`matches`, `total_score`, recommendation, notes). |
| `nodes/match/review/decision.md` | `src/nodes/match/logic.py` and `src/nodes/review_match/logic.py` | Human review surface for checkbox decisions. |
| `nodes/match/review/decision.json` | `src/nodes/review_match/logic.py` | Parsed machine decision envelope used for routing and traceability. |
| `nodes/match/review/rounds/round_<NNN>/decision.md` | `src/nodes/match/logic.py` / `RoundManager` | Immutable per-round review surface snapshots. |
| `nodes/match/review/rounds/round_<NNN>/decision.json` | `src/nodes/review_match/logic.py` | Immutable per-round parsed decision snapshot. |
| `nodes/match/review/rounds/round_<NNN>/feedback.json` | `src/nodes/review_match/logic.py` | Regeneration feedback payload, including optional `patch_evidence`. |
| `nodes/generate_documents/approved/state.json` | `src/nodes/generate_documents/logic.py` | LLM-generated document deltas. |
| `nodes/generate_documents/proposed/cv.md` | `src/nodes/generate_documents/logic.py` | Generated CV markdown draft. |
| `nodes/generate_documents/proposed/motivation_letter.md` | `src/nodes/generate_documents/logic.py` | Generated motivation letter markdown draft. |
| `nodes/generate_documents/proposed/application_email.md` | `src/nodes/generate_documents/logic.py` | Generated email markdown draft. |
| `nodes/generate_documents/assist/proposed/state.json` | `src/nodes/generate_documents/logic.py` | Deterministic text-review indicators. |
| `nodes/generate_documents/assist/proposed/view.md` | `src/nodes/generate_documents/logic.py` | Human-readable text-review table. |
| `nodes/render/proposed/{cv,motivation_letter,application_email}.md` | `src/nodes/render/logic.py` | Render-stage markdown copies. |
| `nodes/render/approved/state.json` | `src/nodes/render/logic.py` | Render envelope with source refs, rendered refs, and content hashes. |
| `nodes/package/approved/state.json` | `src/nodes/package/logic.py` | Package-stage summary pointing to final manifest. |
| `final/{cv,motivation_letter,application_email}.md` | `src/nodes/package/logic.py` | Final packaged markdown deliverables for the current prep flow. |
| `final/manifest.json` | `src/nodes/package/logic.py` | Final artifact inventory and hashes. |
| `graph/run_summary.json` | `ObservabilityService` | Run-level execution summary written by CLI/runtime helpers. |

## Semantic rules in current implementation

### JSON meaning

- Machine-readable state and parser output.
- Used for routing decisions, hashes, and downstream deterministic checks.

### Markdown meaning

- Human review/edit surface (`decision.md`) or human-facing generated content.
- Markdown is still the operator-facing review surface for `review_match`.

### Hash-based review lock (current behavior)

- `review_match` computes expected `source_state_hash` from `nodes/match/approved/state.json`.
- If a `decision.md` has no hash and no checked boxes, the node regenerates it.
- If boxes are checked but hash is missing, it fails closed.
- If the hash mismatches current match state, it fails closed.

## Match regeneration memory flow (implemented)

1. Reviewer marks `Regen` in `nodes/match/review/decision.md`.
2. `review_match` parses and writes `decision.json` + `feedback.json` in the round folder.
3. `match` on `request_regeneration` loads latest feedback via `RoundManager`.
4. Optional `patch_evidence` items are appended into the effective evidence set.
5. New round artifacts are created under `round_<NNN>/`.

## Important current gaps vs target architecture

1. `src/core/io/` exists, but node migration to a single uniform I/O pattern is incomplete.
2. Provenance and observability are partially implemented, but not every node writes a standardized `meta/provenance.json`.
3. The current runnable flow has one active semantic review gate (`review_match`), not the full multi-stage review architecture described in older plans.
4. Several docs in the repo still describe target-state behavior rather than current runtime behavior.

## Practical usage guidance

- For current operational truth, read this file together with:
  - `docs/runtime/graph_flow.md`
  - `docs/runtime/node_io_matrix.md`
  - `docs/operations/tool_interaction_and_known_issues.md`
- For target destination contracts, cross-check target-state docs separately.
