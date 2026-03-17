# Node I/O Matrix (Current State)

## Purpose

This document describes only the node I/O behavior implemented in the current codebase.

Forward-looking/target topology and I/O contracts are tracked under `plan/spec/`.

## Authority scope

- Canonical owner for current node-level I/O visibility in graph context.
- For implementation-first data semantics, also see `docs/reference/data_management_actual_state.md`.

## Legend

- Execution class:
  - `LLM` = step uses an LLM.
  - `NLLM-D` = non-LLM deterministic step.
  - `NLLM-ND` = non-LLM bounded-nondeterministic step.
- Review gate: whether the node requires explicit HITL review before flow continues.
- Paths are relative to `data/jobs/<source>/<job_id>/`.

## Current implemented matrix

Current operational graph helper is `create_prep_match_app()` in `src/graph.py`:

`scrape -> translate_if_needed -> extract_understand -> match -> review_match -> generate_documents -> package`

with `review_match.approve -> generate_documents`.

| Node | Execution Class | Required Inputs (current code) | Outputs (current code) | Review Gate | Downstream Consumers | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `scrape` | `NLLM-ND` | `state.source_url` | GraphState: `ingested_data` | No | `translate_if_needed` | `run_logic` currently updates state only; canonical disk writes for scrape artifacts are produced by existing batch/backfill workflows, not by this node function directly. |
| `translate_if_needed` | `NLLM-ND` | `state.ingested_data.raw_text`, optional `state.target_language` | GraphState: updated `ingested_data` | No | `extract_understand` | State-only transformation in node logic. |
| `extract_understand` | `LLM` | `state.job_id`, `state.ingested_data.raw_text`, optional `state.active_feedback` | GraphState: `extracted_data` | No | `match` | State-only output in node logic. |
| `match` | `LLM` | `state.job_id`, `state.extracted_data.requirements`, `state.my_profile_evidence`; optional regeneration context | GraphState: `matched_data`; Data Plane: `nodes/match/approved/state.json`, `nodes/match/review/decision.md`, `nodes/match/review/rounds/round_<NNN>/decision.md` | Yes (`review_match`) | `review_match` | Uses `RoundManager`; regeneration requires actionable patch feedback. |
| `review_match` | `NLLM-D` | `state.source`, `state.job_id`, `state.matched_data`, `nodes/match/review/decision.md` | GraphState: `review_decision`, `last_decision`, `active_feedback`, `artifact_refs`; Data Plane: `nodes/match/review/decision.json`, `rounds/round_<NNN>/decision.json`, `rounds/round_<NNN>/feedback.json` | Decision parser | `match` (regen), `generate_documents` (approve), `END` (reject) | Enforces stale-hash lock when `source_state_hash` is present; auto-regenerates unreviewed legacy markdown without hash. |
| `generate_documents` | `LLM` + deterministic rendering | `state.matched_data`, latest match decision (`state.last_decision` or `nodes/match/review/decision.json`), profile base data | Data Plane: `nodes/generate_documents/approved/state.json`, `nodes/generate_documents/proposed/*.md`, `nodes/generate_documents/assist/proposed/{state.json,view.md}`; GraphState: `document_deltas`, `text_review_indicators` | No | `package` | Produces CV/letter/email draft markdown and deterministic text-review indicators after approved matching. |
| `package` (prep terminal) | `NLLM-D` | GraphState only | GraphState: `status=completed` | No | End | Current prep terminal does not package final documents. |

## Current non-negotiable checks

1. `match` and `review_match` fail closed on malformed regeneration/decision inputs.
2. Review parsing rejects invalid checkbox markup and stale-hash mismatches.
3. Regeneration requires at least one actionable patch feedback entry.

## Planning pointer

Target-state node I/O contract and full topology matrix:

- `plan/spec/node_io_target_matrix.md`
