# Canonical Documentation Map

This file defines which docs describe current runtime truth, which docs are target-state/design references, and which docs are historical or planning material.

## Current runtime truth

Use these first when you need to know what actually runs today.

- `README.md`
- `docs/graph/nodes_summary.md`
- `docs/graph/node_io_matrix.md`
- `docs/graph/match_review_cycle.md`
- `docs/reference/data_management_actual_state.md`
- `docs/operations/tool_interaction_and_known_issues.md`
- `docs/architecture/core_io_and_provenance_manager.md`

## Current repo navigation / status map

- `docs/index/README.md`
- `docs/index/canonical_map.md`

## Current UI sandbox docs

These are current for sandbox/workbench behavior, not for pipeline runtime truth.

- `docs/architecture/node_editor_behavior_spec.md`
- `docs/architecture/node_editor_customization_and_architecture.md`
- `docs/architecture/node_editor_compliance_matrix.md`
- `docs/UI_plan/README.md`

## Target-state / design references

These are useful design-intent docs, but they should not be treated as exact current runtime behavior unless they explicitly say so.

- `docs/architecture/graph_state_contract.md`
- `docs/reference/artifact_schemas.md`
- `docs/templates/node_template_discipline.md`
- `docs/templates/taxonomy_template_catalog.md`
- `docs/business_rules/sync_json_md.md`
- `docs/business_rules/feedback_memory.md`
- `docs/philosophy/project_overview.md`
- `docs/philosophy/structure_and_rationale.md`

## Active planning / migration docs

These are planning records, not runtime truth.

- `plan/subplan/deterministic_parity_migration_from_phd.md`
- `plan/subplan/review_ui_and_flow_observability.md`
- `plan/subplan/playwright_scraping_execution_blueprint.md`
- `plan/subplan/langchain_runtime_migration_plan.md`
- `plan/subplan/langchain_langgraph_adoption_evaluation.md`
- `plan/adr/adr_001_ui_first_knowledge_graph_langchain.md`
- `plan/adr_001_execution_tracker.md`

## Historical / status-snapshot docs

These should be read as dated snapshots unless updated explicitly.

- `plan/phd2_stepwise_plan.md`
- `plan/index_checklist.md`
- `plan/step6_13_delta_generation_and_text_reviewers.md`
- `plan/step6_13_implementation_notes.md`

## Rule

If a document conflicts with the current runtime truth set above, trust the current runtime truth set and mark the conflicting doc as target-state, planning, or historical.
