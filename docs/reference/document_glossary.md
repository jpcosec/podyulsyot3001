# Document and Artifact Glossary

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

- `docs/architecture/structure_and_rationale.md`: layer boundaries, design rules, failure taxonomy, and rationale.
- `docs/architecture/graph_definition.md`: graph flow, node contracts, review branches, directives, and invariants.
- `docs/architecture/node_io_matrix.md`: node-by-node input/output contracts and downstream consumers.
- `docs/architecture/artifact_schemas.md`: full JSON schemas for every pipeline artifact.
- `docs/architecture/claim_admissibility_and_policy.md`: claim classes, evidence compatibility, coverage transitions, downstream policy.
- `docs/architecture/feedback_memory.md`: feedback event schema, storage model, retrieval strategy, conflict model.
- `docs/architecture/sync_json_md.md`: JSON/Markdown sync service API, staleness protection, parser requirements.

## Overview docs

- `docs/overview/project_overview.md`: what the project is and how it works end-to-end.
- `docs/overview/document_glossary.md`: this glossary of document and artifact meanings.

## Prompt docs

- `docs/prompts/README.md`: prompt pack index and design principles.
- `docs/prompts/matcher.md` through `docs/prompts/feedback_distiller.md`: per-prompt role, inputs, outputs, and constraints.

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
