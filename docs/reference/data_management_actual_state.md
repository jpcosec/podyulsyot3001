# Data Management and Semantics (Actual Codebase State)

Related references:

- `src/core/graph/state.py`
- `src/graph.py`
- `src/cli/run_prep_match.py`
- `src/nodes/match/logic.py`
- `src/nodes/review_match/logic.py`
- `src/nodes/generate_documents/logic.py`
- `docs/reference/artifact_schemas.md` (target-state contract)
- `docs/architecture/core_io_and_provenance_manager.md` (target-state I/O layer)

## Purpose

This document describes how data is actually stored, moved, and interpreted in the current codebase.

It is intentionally implementation-first. Where it differs from target architecture docs, this file records the current behavior without normalization.

## Authority scope

- Canonical owner for **current runtime data behavior**.
- Not the owner of final/target schema design (that remains `docs/reference/artifact_schemas.md`).

## Current execution surface (implemented)

The executable graph helper in daily use is the prep-match flow:

1. `scrape`
2. `translate_if_needed`
3. `extract_understand`
4. `match`
5. `review_match`

Implemented by:

- `src/graph.py` via `build_prep_match_node_registry()`, `create_prep_match_app()`, `run_prep_match()`.
- `src/cli/run_prep_match.py` for operator execution and resume.

`generate_documents` exists as a node package (`src/nodes/generate_documents/`) with artifact writes, but it is not included in the prep-match registry.

## Storage roots and ownership

### Job workspace root

- Root: `data/jobs/<source>/<job_id>/`
- Example currently populated: `data/jobs/tu_berlin/*`

### Profile base snapshot

- Canonical profile snapshot used by utilities and `generate_documents` fallback:
  - `data/reference_data/profile/base_profile/profile_base_data.json`

### Checkpoints

- Default runtime checkpoint path for prep-match CLI:
  - `data/jobs/<source>/<job_id>/graph/checkpoint.sqlite`

## Control-plane data (GraphState) in current code

`GraphState` is defined in `src/core/graph/state.py`.

Current state includes both routing metadata and transient payload fields:

- Routing/identity: `source`, `job_id`, `run_id`, `current_node`, `status`, `review_decision`, `pending_gate`, `error_state`, `artifact_refs`.
- Transient payloads: `ingested_data`, `extracted_data`, `matched_data`, `my_profile_evidence`, `last_decision`, `active_feedback`.

Meaning:

- The control plane is partially aligned with the target model (routing fields exist),
- but still carries semantic payloads in memory during execution.

## Data-plane artifacts currently written and consumed

All paths below are relative to `data/jobs/<source>/<job_id>/`.

| Path | Producer in current codebase | Meaning / usage |
|---|---|---|
| `raw/raw.html` | Existing batch/backfill workflows (not node-local write in current `scrape` logic) | Raw fetched HTML source for audit/debug. |
| `raw/source_text.md` | Existing batch/backfill workflows | Human-readable extracted text input for understanding/match audits. |
| `raw/language_check.json` | Existing batch/backfill workflows | Translation/language detection diagnostics. |
| `nodes/scrape/approved/state.json` | Existing batch/backfill workflows | Serialized scrape output (`source_url`, `original_language`, `raw_text`, metadata). |
| `nodes/translate_if_needed/approved/state.json` | Existing batch/backfill workflows | Scrape payload plus translation flags (`translated`, `translated_to`). |
| `nodes/extract_understand/approved/state.json` | Existing batch/backfill workflows | Structured job understanding (`requirements`, `constraints`, `risk_areas`). |
| `nodes/match/approved/state.json` | `src/nodes/match/logic.py` | Canonical persisted match envelope (`matches`, `total_score`, recommendation, notes). |
| `nodes/match/review/decision.md` | `src/nodes/match/logic.py` (mirror from latest round) and `src/nodes/review_match/logic.py` (auto-regeneration when needed) | Human review surface for checkbox decisions. |
| `nodes/match/review/rounds/round_<NNN>/decision.md` | `src/nodes/match/logic.py` | Immutable per-round review surface snapshots. |
| `nodes/match/review/decision.json` | `src/nodes/review_match/logic.py` | Parsed machine decision envelope used for routing and traceability. |
| `nodes/match/review/rounds/round_<NNN>/decision.json` | `src/nodes/review_match/logic.py` | Immutable per-round parsed decision snapshot. |
| `nodes/match/review/rounds/round_<NNN>/feedback.json` | `src/nodes/review_match/logic.py` | Regeneration feedback payload (including optional `patch_evidence`). |
| `nodes/generate_documents/approved/state.json` | `src/nodes/generate_documents/logic.py` | LLM-generated document deltas (`cv_summary`, `cv_injections`, letter/email deltas). |
| `nodes/generate_documents/proposed/cv.md` | `src/nodes/generate_documents/logic.py` | Deterministically rendered CV draft content. |
| `nodes/generate_documents/proposed/motivation_letter.md` | `src/nodes/generate_documents/logic.py` | Deterministically rendered letter draft content. |
| `nodes/generate_documents/proposed/application_email.md` | `src/nodes/generate_documents/logic.py` | Deterministically rendered email draft content. |
| `nodes/generate_documents/assist/proposed/state.json` | `src/nodes/generate_documents/logic.py` | Deterministic text-review indicators (`grounding`, `tone`, `format`, etc.). |
| `nodes/generate_documents/assist/proposed/view.md` | `src/nodes/generate_documents/logic.py` | Human-readable table of deterministic text-review indicators. |
| `application/cv.pdf` | `src/cli/render_cv.py` | Rendered CV output for delivery. |
| `application/motivation_letter.pdf` | `src/cli/render_letter.py` | Rendered motivation letter PDF output. |
| `render_build/*` | render CLIs/tools | Intermediate render artifacts (build workspace). |

### Observed repository snapshot (this checkout)

- Populated job workspace currently observed under `data/jobs/tu_berlin/` with jobs such as `201578`, `201588`, `201601`, `201606`, `201637`, `201661`, `201695`.
- Persisted artifacts in those folders are primarily scrape/translate/extract/match approved states plus match review markdown.
- No committed `nodes/match/review/decision.json` or `rounds/*/feedback.json` files are currently present in the tracked job snapshot, which indicates parse/resume outputs are generated at runtime and are not yet part of the committed dataset.

## Semantic rules in current implementation

### JSON meaning

- Machine-readable state and parser output.
- Used for routing decisions (`review_decision`) and regeneration feedback consumption.

### Markdown meaning

- Human review/edit surface (`decision.md`) or human-facing rendered drafts.
- Markdown is parsed deterministically in `review_match` for checkbox decisions.

### Hash-based review lock (current behavior)

- `review_match` computes expected `source_state_hash` from `nodes/match/approved/state.json`.
- If a `decision.md` has no hash and no checked boxes, the node regenerates it.
- If boxes are checked but hash is missing, it fails closed and asks for regeneration/re-apply.
- If hash mismatches current state, it fails closed.

## Match regeneration memory flow (implemented)

1. Reviewer marks `Regen` in `nodes/match/review/decision.md`.
2. `review_match` parses and writes `decision.json` + `feedback.json` in round folder.
3. `match` on `request_regeneration` loads latest feedback via `RoundManager`.
4. Optional `patch_evidence` items are appended into effective evidence set.
5. New round artifacts are created under `round_<NNN>/`.

## Important current gaps vs target architecture

1. `src/core/io/` is not implemented yet (no `WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, `ProvenanceService`).
2. Provenance files (`nodes/<node>/meta/provenance.json`) are not generated in current runtime path.
3. Generators do not consistently follow `proposed/ -> review/ -> approved/` layering; current matching persistence uses `nodes/match/approved/state.json` as primary persisted state.
4. The current repository data snapshot contains legacy `decision.md` files without front matter hash; runtime hardening handles this during review resume.

## Practical usage guidance

- For current operational truth, read this file first.
- For target destination contracts, cross-check:
  - `docs/reference/artifact_schemas.md`
  - `docs/architecture/core_io_and_provenance_manager.md`
  - `docs/architecture/graph_state_contract.md`
