# Node I/O Matrix

## Purpose

This document separates:

1. **Current implemented I/O behavior** (what runs today), and
2. **Target-state I/O contract** (where architecture is headed).

This split is intentional to avoid mixing runnable behavior with planned design.

## Authority scope

- Canonical owner for node-level I/O visibility in graph context.
- For implementation-first data semantics, also see `docs/reference/data_management_actual_state.md`.
- For target artifact schemas, see `docs/reference/artifact_schemas.md`.

It complements:

- `docs/graph/nodes_summary.md` (flow and routing semantics)
- `docs/philosophy/structure_and_rationale.md` (architectural boundaries)

JSON artifacts are canonical. Markdown artifacts are human-facing review surfaces.

## Legend

- Execution class:
  - `LLM` = step uses an LLM.
  - `NLLM-D` = non-LLM deterministic step.
  - `NLLM-ND` = non-LLM bounded-nondeterministic step.
- Review gate: whether the node requires an explicit HITL review decision before flow continues.
- Paths are shown relative to `data/jobs/<source>/<job_id>/`.

## A) Current implemented matrix (actual codebase)

Current operational graph helper is `create_prep_match_app()` in `src/graph.py`:

`scrape -> translate_if_needed -> extract_understand -> match -> review_match`

with `review_match.approve -> package` (terminal node in this subgraph).

| Node | Execution Class | Required Inputs (current code) | Outputs (current code) | Review Gate | Downstream Consumers | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `scrape` | `NLLM-ND` | `state.source_url` | GraphState: `ingested_data` | No | `translate_if_needed` | `run_logic` currently updates state only; canonical disk writes for scrape artifacts are produced by existing batch/backfill workflows, not by this node function directly. |
| `translate_if_needed` | `NLLM-ND` | `state.ingested_data.raw_text`, optional `state.target_language` | GraphState: updated `ingested_data` | No | `extract_understand` | State-only transformation in node logic. |
| `extract_understand` | `LLM` | `state.job_id`, `state.ingested_data.raw_text`, optional `state.active_feedback` | GraphState: `extracted_data` | No | `match` | State-only output in node logic. |
| `match` | `LLM` | `state.job_id`, `state.extracted_data.requirements`, `state.my_profile_evidence`; optional regeneration context | GraphState: `matched_data`; Data Plane: `nodes/match/approved/state.json`, `nodes/match/review/decision.md`, `nodes/match/review/rounds/round_<NNN>/decision.md` | Yes (`review_match`) | `review_match` | Uses `RoundManager`; regeneration requires actionable patch feedback. |
| `review_match` | `NLLM-D` | `state.source`, `state.job_id`, `state.matched_data`, `nodes/match/review/decision.md` | GraphState: `review_decision`, `last_decision`, `active_feedback`, `artifact_refs`; Data Plane: `nodes/match/review/decision.json`, `rounds/round_<NNN>/decision.json`, `rounds/round_<NNN>/feedback.json` | Decision parser | `match` (regen), `package` (approve), `END` (reject) | Enforces stale-hash lock when `source_state_hash` is present; auto-regenerates unreviewed legacy markdown without hash. |
| `package` (prep terminal) | `NLLM-D` | GraphState only | GraphState: `status=completed` | No | End | Current prep terminal does not package final documents. |

### Implemented but not wired in prep-match registry

| Node | Execution Class | Required Inputs (current code) | Outputs (current code) | Review Gate | Notes |
| --- | --- | --- | --- | --- | --- |
| `generate_documents` | `LLM` + deterministic rendering | `state.matched_data`, latest match decision (`state.last_decision` or `nodes/match/review/decision.json`), profile base data | Data Plane: `nodes/generate_documents/approved/state.json`, `nodes/generate_documents/proposed/*.md`, `nodes/generate_documents/assist/proposed/{state.json,view.md}`; GraphState: `document_deltas`, `text_review_indicators` | No dedicated review node in current wiring | Node package exists and is tested, but it is not included in `build_prep_match_node_registry()`. |

## B) Target-state matrix (architectural contract)

| Node | Execution Class | Required Inputs | Proposed Outputs | Review Gate | Approved Outputs | Downstream Consumers | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `scrape` | `NLLM-ND` | External URL/listing source | `raw/raw.html`, `raw/source_text.md`, `nodes/scrape/proposed/state.json` | No | `nodes/scrape/approved/state.json` | `translate_if_needed` | Source prep stage; network-dependent variability is expected. |
| `translate_if_needed` | `NLLM-ND` | `nodes/scrape/approved/state.json` | `nodes/translate_if_needed/proposed/state.json` | No | `nodes/translate_if_needed/approved/state.json` | `extract_understand` | Normalizes text language only when needed. |
| `extract_understand` | `LLM` | `nodes/translate_if_needed/approved/state.json` | `nodes/extract_understand/proposed/state.json` | No | `nodes/extract_understand/approved/state.json` | `match` | Produces structured understanding (requirements/constraints/risk areas). |
| `match` | `LLM` | `nodes/extract_understand/approved/state.json`, profile context | `nodes/match/proposed/state.json`, `nodes/match/proposed/view.md`, `nodes/match/review/decision.md` | Yes (`review_match`) | N/A (approval happens in review node) | `review_match` | Must not silently fallback to fake success. |
| `review_match` | `NLLM-D` | `nodes/match/proposed/state.json`, `nodes/match/review/decision.md` | `nodes/match/review/decision.json` | Decision parser | `nodes/review_match/approved/state.json`, `nodes/review_match/meta/provenance.json` | `build_application_context` or loop/stop | Enforces decision validity and stale-hash protection. |
| `build_application_context` | `LLM` | `nodes/review_match/approved/state.json`, profile constraints | `nodes/build_application_context/proposed/state.json`, `nodes/build_application_context/proposed/view.md`, `nodes/build_application_context/review/decision.md` | Yes (`review_application_context`) | N/A (approval happens in review node) | `review_application_context` | Creates grounded strategy/context from approved mapping. |
| `review_application_context` | `NLLM-D` | `nodes/build_application_context/proposed/state.json`, `nodes/build_application_context/review/decision.md` | `nodes/build_application_context/review/decision.json` | Decision parser | `nodes/review_application_context/approved/state.json`, `nodes/review_application_context/meta/provenance.json` | `generate_motivation_letter`, `tailor_cv`, `draft_email` | Must preserve reviewed decisions deterministically. |
| `generate_motivation_letter` | `LLM` | `nodes/review_application_context/approved/state.json` | `nodes/generate_motivation_letter/proposed/state.json`, `nodes/generate_motivation_letter/proposed/letter.md`, `nodes/generate_motivation_letter/proposed/view.md`, `nodes/generate_motivation_letter/review/decision.md` | Yes (`review_motivation_letter`) | N/A (approval happens in review node) | `review_motivation_letter` | Must reference approved claims only. |
| `review_motivation_letter` | `NLLM-D` | `nodes/generate_motivation_letter/proposed/state.json`, `nodes/generate_motivation_letter/review/decision.md` | `nodes/generate_motivation_letter/review/decision.json` | Decision parser | `nodes/review_motivation_letter/approved/state.json`, `nodes/review_motivation_letter/meta/provenance.json` | `tailor_cv`, `draft_email`, `render` | Applies review decisions and records provenance. |
| `tailor_cv` | `LLM` | `nodes/review_application_context/approved/state.json`, `nodes/review_motivation_letter/approved/state.json` | `nodes/tailor_cv/proposed/state.json`, `nodes/tailor_cv/proposed/to_render.md`, `nodes/tailor_cv/proposed/view.md`, `nodes/tailor_cv/review/decision.md` | Yes (`review_cv`) | N/A (approval happens in review node) | `review_cv` | Produces CV proposal that must pass explicit review. |
| `review_cv` | `NLLM-D` | `nodes/tailor_cv/proposed/state.json`, `nodes/tailor_cv/proposed/to_render.md`, `nodes/tailor_cv/review/decision.md` | `nodes/tailor_cv/review/decision.json` | Decision parser | `nodes/review_cv/approved/state.json`, `nodes/review_cv/approved/to_render.md`, `nodes/review_cv/meta/provenance.json` | `draft_email`, `review_email`, `render` | Enforces CV pass/regenerate/reject decisions. |
| `draft_email` | `LLM` | `nodes/review_application_context/approved/state.json`, `nodes/review_motivation_letter/approved/state.json`, `nodes/review_cv/approved/state.json` | `nodes/draft_email/proposed/state.json`, `nodes/draft_email/proposed/application_email.md`, `nodes/draft_email/proposed/view.md`, `nodes/draft_email/review/decision.md` | Yes (`review_email`) | N/A (approval happens in review node) | `review_email` | Must be job-specific, no generic template fallback. |
| `review_email` | `NLLM-D` | `nodes/draft_email/proposed/state.json`, `nodes/draft_email/proposed/application_email.md`, `nodes/draft_email/review/decision.md` | `nodes/draft_email/review/decision.json` | Decision parser | `nodes/review_email/approved/state.json`, `nodes/review_email/approved/application_email.md`, `nodes/review_email/meta/provenance.json` | `render`, delivery | Enforces email pass/regenerate/reject decisions. |
| `render` | `NLLM-D` | `nodes/review_cv/approved/to_render.md`, `nodes/review_motivation_letter/approved/state.json`, `nodes/review_email/approved/state.json` | `nodes/render/proposed/state.json` | No | `nodes/render/approved/state.json`, `nodes/render/meta/provenance.json`, `final/cv.pdf|md`, `final/motivation_letter.pdf|md` | `package` | Final renderer can target DOCX/PDF and retain metadata. |
| `package` | `NLLM-D` | Render outputs from `final/` | `nodes/package/proposed/state.json` | No | `nodes/package/approved/state.json`, `nodes/package/meta/provenance.json`, `final/Final_Application.pdf|md`, `final/manifest.json` | End of graph | Must include hash manifest and reproducible package metadata. |

## Review-gated routing rules (target state)

For `review_match`, `review_application_context`, `review_motivation_letter`, `review_cv`, and `review_email`:

- `approve` -> continue to next stage.
- `request_regeneration` -> return to corresponding generator node.
- `reject` -> terminate run.

## Non-negotiable checks

### Current implemented path

1. `match` and `review_match` must fail closed on malformed regeneration/decision inputs.
2. Review parsing must reject invalid checkbox markup and stale-hash mismatches.
3. Regeneration requires at least one actionable patch feedback entry.

### Target-state path

1. Required canonical files exist.
2. Output JSON validates against node contract schema.
3. Review nodes reject malformed or stale decisions.
4. Approved artifacts carry provenance where required.
5. Downstream reads only from `approved/` paths.
