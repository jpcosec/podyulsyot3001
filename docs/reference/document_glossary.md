# Document and Artifact Glossary

> Status note (2026-03-20): this glossary mixes current and target-state artifact descriptions. Some entries below describe planned review, provenance, or finalization conventions that are not uniformly implemented across the current runtime. Use `docs/reference/data_management_actual_state.md` for current artifact behavior.


## Purpose

This glossary explains what each documentation file and runtime artifact means.

It is the quick semantic reference for operators and developers.

## Repository documentation files

## Top-level

- `README.md`: project entrypoint, system overview, and documentation index.
- `changelog.md`: record of major changes and documentation updates.

## Plan folder

- `plan/phd2_stepwise_plan.md`: stepwise implementation and approval plan.
- `plan/index_checklist.md`: compact checklist of all execution steps.

## Architecture docs

- `docs/philosophy/structure_and_rationale.md`: layer boundaries, design rules, failure taxonomy, and rationale.
- `docs/graph/nodes_summary.md`: graph flow, node contracts, review branches, directives, and invariants.
- `docs/graph/node_io_matrix.md`: node-by-node input/output contracts and downstream consumers.
- `docs/architecture/graph_reactivity_protocol.md`: distinguishes immediate present-case corrections (emergent evidence) from deferred learning updates (feedback memory).
- `docs/architecture/graph_state_contract.md`: canonical control-plane GraphState ledger and checkpoint identity rules.
- `docs/reference/artifact_schemas.md`: full JSON schemas for every pipeline artifact.
- `docs/reference/contract_composition_framework.md`: envelope/primitive composition rules for node `contract.py` schemas.
- `docs/reference/extracting_contract_case_job_understanding.md`: concrete extracting-case contract example for `extract_understand`.
- `docs/reference/matching_contract_case_matrix_and_escape_hatch.md`: concrete matching-case contract with matrix modeling, source-text mirror, and deterministic escape-hatch regeneration flow.
- `docs/reference/redacting_contract_case_traceable_dual_output.md`: concrete redacting-case contract with style strategy input, dual JSON+Markdown envelope, and deterministic consumed-evidence checks.
- `docs/reference/review_contract_case_decision_and_assistance.md`: concrete reviewing-case contract separating deterministic decisions (`DecisionEnvelope`) from optional LLM assistance (`ReviewAssistEnvelope`).
- `docs/business_rules/claim_admissibility_and_policy.md`: claim classes, evidence compatibility, coverage transitions, downstream policy.
- `docs/business_rules/feedback_memory.md`: feedback event schema, storage model, retrieval strategy, conflict model.
- `docs/business_rules/sync_json_md.md`: JSON/Markdown sync service API, staleness protection, parser requirements.

## Overview docs

- `docs/philosophy/project_overview.md`: what the project is and how it works end-to-end.
- `docs/reference/document_glossary.md`: this glossary of document and artifact meanings.

## Prompt docs

- `docs/templates/prompts/README.md`: prompt pack index and design principles.
- `docs/templates/prompts/matcher.md` through `docs/templates/prompts/feedback_distiller.md`: per-prompt role, inputs, outputs, and constraints.

## Operations docs

- `docs/operations/tool_interaction_and_known_issues.md`: CLI interaction, run-review-resume flow, and troubleshooting guide.

## Runtime artifact documents (per job)

Base path:

- `data/jobs/<source>/<job_id>/`

## Source artifacts

- `raw/raw.html`: raw page capture from source website.
- `raw/source_text.md`: normalized extracted source text.
- `raw/extracted.json`: structured extraction of source content.
- `raw/language_check.json`: language detection/normalization metadata.

## Node artifact folders

Node base:

- `nodes/<node>/`

Subfolders:

- `input/`: optional frozen upstream snapshots for reproducibility.
- `proposed/`: machine-generated proposal artifacts.
- `review/`: human review inputs and parser outputs.
- `approved/`: canonical approved artifacts used downstream.
- `meta/`: provenance and auxiliary metadata.

## Canonical per-node files

- `proposed/state.json`: machine-readable canonical proposal.
- `proposed/view.md`: reviewer-readable representation of proposal.
- `review/decision.md`: human-edited decision form.
- `review/decision.json`: parsed and validated decision payload.
- `approved/state.json`: approved canonical output consumed by next nodes.
- `meta/provenance.json`: trace data (producer, run id, input hashes, references).

## Profile artifacts

- `profile/profile_base_data.json`: canonical profile knowledge base with personal, education, experience, publications, skills, and languages.

## Feedback artifacts

- `feedback/events/<stage>/<timestamp>.json`: structured feedback events from review stages.
- `feedback/active_memory.yaml`: distilled reusable rules for prompt injection.
- `feedback/conflicts.yaml`: explicit feedback conflicts requiring human resolution.

## Runtime and final artifacts

- `runtime/checkpoints/`: graph state required for interrupts/resume.
- `final/`: final delivery artifacts produced by render/package.
- `final/manifest.json`: hashes and inventory of final deliverables.

## Review decision meaning

- `approve`: accept proposal as-is and continue.
- `request_regeneration`: send flow back to generating node.
- `reject`: stop the current run.

## Quick interpretation rules

1. JSON is canonical; markdown is the human interface.
2. `approved/` is the only safe input for downstream nodes.
3. Missing or stale review/metadata files are blocking errors.
4. Final artifacts are valid only when manifest and provenance are consistent.
