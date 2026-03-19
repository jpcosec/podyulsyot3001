# PhD 2.0 (Rebuild Workspace)

This repository is the clean rebuild track for the PhD application pipeline.

The goal is to produce high-quality application artifacts (match mapping, application context, motivation letter, tailored CV, email, rendered output, package) through a graph workflow that combines deterministic guarantees with human-in-the-loop (HITL) review.

## Why this rebuild exists

The previous 2.0 attempt kept a strong scaffold but allowed wax-model behavior: outputs looked structurally correct while core semantics were still placeholder or hardcoded. This workspace rebuilds the same target architecture with strict step gates and explicit human approval.

## What the project is

PhD 2.0 is a node-based pipeline with three domains:

- `src/core`: deterministic contracts, parsing, validation, provenance, render/package, review sync.
- `src/ai`: LLM runtime, prompt-local AI nodes, graph orchestration.
- `src/interfaces`: CLI/operator commands to run, review, resume, and inspect.

## How it is meant to work

1. Ingest raw job artifacts.
2. Extract and normalize structured understanding.
3. Translate when needed.
4. Generate LLM artifacts at specific nodes.
5. Pause at review gates and require explicit decisions.
6. Continue only with approved state.
7. Render final artifacts and package deliverables with provenance.

Graph-level execution is resumable and auditable.

## Graph summary

Core path:

`scraping -> ingest -> extract_understand -> translate -> match -> review_match -> build_application_context -> review_application_context -> generate_motivation_letter -> review_motivation_letter -> tailor_cv -> review_cv -> draft_email -> review_email -> render -> package`

Review branches:

- `approve` -> continue.
- `request_regeneration` -> loop back to previous generation node.
- `reject` -> stop.

## Current status

- Rebuild plan is active and approval-gated.
- Documentation is the source of truth while implementation progresses.
- Step tracking is maintained under `plan/`.

## Documentation index

Start here:

- Master docs index: `docs/index/README.md`
- Conceptual tree: `docs/index/conceptual_tree.md`

## Plan (stepwise implementation)

- Rebuild master plan: `plan/phd2_stepwise_plan.md`
- Step index checklist: `plan/index_checklist.md`
- Worktree planning protocol: `plan/worktree_planning_protocol.md`
- Deterministic parity migration: `plan/subplan/deterministic_parity_migration_from_phd.md`
- JSON-first scraping subsystem migration: `plan/subplan/json_first_scraping_subsystem_migration.md`
- Review UI + flow observability: `plan/subplan/review_ui_and_flow_observability.md`
- LangChain/LangGraph evaluation: `plan/subplan/langchain_langgraph_adoption_evaluation.md`

## Philosophy (why)

- Project overview, system diagram, and working model: `docs/philosophy/project_overview.md`
- Architecture boundaries, failure taxonomy, and rationale: `docs/philosophy/structure_and_rationale.md`
- Execution taxonomy (abstract): `docs/philosophy/execution_taxonomy_abstract.md`
- Template architecture problem statement: `docs/philosophy/template_problem_statement.md`

## Graph (what runs)

- Graph definition, node contracts, and review directives: `docs/graph/nodes_summary.md`
- Node-by-node I/O matrix: `docs/graph/node_io_matrix.md`

## Templates (how to implement)

- Node template discipline: `docs/templates/node_template_discipline.md`
- Taxonomy template catalog: `docs/templates/taxonomy_template_catalog.md`
- Taxonomic LLM templates (deep): `docs/templates/llm/README.md`
- Prompt specifications: `docs/templates/prompts/README.md`

## Business rules (what is allowed)

- Claim admissibility and policy: `docs/business_rules/claim_admissibility_and_policy.md`
- Feedback memory system: `docs/business_rules/feedback_memory.md`
- `sync_json_md` service: `docs/business_rules/sync_json_md.md`

## Node editor sandbox

- Behavior specification: `docs/architecture/node_editor_behavior_spec.md`
- Customization and architecture guide: `docs/architecture/node_editor_customization_and_architecture.md`
- Compliance matrix: `docs/architecture/node_editor_compliance_matrix.md`

## Reference

- Actual runtime data behavior (current codebase): `docs/reference/data_management_actual_state.md`
- Artifact JSON schemas: `docs/reference/artifact_schemas.md`
- Document and artifact glossary: `docs/reference/document_glossary.md`
- Core I/O and provenance data plane: `docs/architecture/core_io_and_provenance_manager.md`
- Source dependency map for impact-based testing: `src/DEPENDENCY_GRAPH.md`

## Operate the tool

- CLI workflow and troubleshooting: `docs/operations/tool_interaction_and_known_issues.md`
- Non-LLM recovery demo (reviewable): `docs/operations/non_llm_recovery_demo.md`
- UI workbench Phase 0 bootstrap: `docs/operations/ui_workbench_phase0_bootstrap.md`
- Start full local stack: `./scripts/dev-all.sh`
- Start UI + API only: `./scripts/dev.sh`
- Repo protocol check: `python -m src.cli.check_repo_protocol`

## Local enforcement setup

1. Install pre-commit hooks:
   - `pip install pre-commit`
   - `pre-commit install --hook-type pre-commit --hook-type pre-push`
2. Optional git native hooks path:
   - `git config core.hooksPath .githooks`

`pre-push` enforces a clean working tree (`python -m src.cli.check_repo_protocol --require-clean-tree`), which blocks pushes when local changes are not committed.

## Cross-project propagation

To propagate the enforcement pack to sibling repositories:

1. Dry run:
   - `python -m src.cli.propagate_protocol_pack --discover`
2. Apply to all discovered repos (excluding this one):
   - `python -m src.cli.propagate_protocol_pack --discover --apply --overwrite`

The propagation command installs:

- `.pre-commit-config.yaml`
- `.githooks/pre-commit`
- `.githooks/pre-push`
- `src/cli/check_repo_protocol.py` (baseline checker)
- `.github/workflows/repo-protocol.yml` (unless `--skip-workflow`)

## Core principles

1. Deterministic correctness before LLM trust.
2. Strict node shape (`contract -> logic -> node`) with centralized I/O in `src/core/io/`.
3. No silent fallback-to-success paths.
4. LLM semantic acceptance is HITL-only.
5. No advancement without explicit human approval.

## Repository rules

- Keep high-level cross-cutting docs under `docs/`.
- Add module-specific docs alongside the corresponding module when code lands.
- Record major changes in `changelog.md`.
