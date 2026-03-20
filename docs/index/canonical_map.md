# Canonical Documentation Map

This file defines which docs describe current runtime truth, which docs are target-state/design references, and which docs are historical or planning material.

## Current runtime truth

Use these first when you need to know what actually runs today.

- `README.md`
- `docs/runtime/graph_flow.md`
- `docs/runtime/node_io_matrix.md`
- `docs/runtime/match_review_cycle.md`
- `docs/runtime/data_management.md`
- `docs/operations/tool_interaction_and_known_issues.md`
- `docs/runtime/core_io_and_provenance.md`

## Current repo navigation / status map

- `docs/index/README.md`
- `docs/index/canonical_map.md`

## Current policy notes

- `docs/policy/feedback_memory.md`

## Current UI sandbox docs

These are current for sandbox/workbench behavior, not for pipeline runtime truth.

- `docs/ui/node_editor_behavior_spec.md`
- `docs/ui/node_editor_customization_and_architecture.md`
- `docs/ui/node_editor_compliance_matrix.md`
- `apps/review-workbench/src/sandbox/README.md`

## Target-state / design references

These are useful design-intent docs, but they should not be treated as exact current runtime behavior unless they explicitly say so.

- `plan/runtime/graph_state_contract.md`
- `plan/runtime/artifact_schemas.md`
- `plan/runtime/node_template_discipline.md`
- `plan/runtime/templates/taxonomy_template_catalog.md`
- `plan/runtime/sync_json_md.md`
- `plan/runtime/claim_admissibility_and_policy.md`
- `plan/archive/project_overview.md`
- `plan/archive/structure_and_rationale.md`

## Active planning / migration docs

These are planning records, not runtime truth.

- `plan/subplan/deterministic_parity_migration_from_phd.md`
- `plan/subplan/review_ui_and_flow_observability.md`
- `plan/subplan/playwright_scraping_execution_blueprint.md`
- `plan/subplan/langchain_runtime_migration_plan.md`
- `plan/subplan/langchain_langgraph_adoption_evaluation.md`
- `plan/adr/adr_001_ui_first_knowledge_graph_langchain.md`
- `plan/adr/adr_001_ui_first_knowledge_graph_langchain_status.md`
- `plan/ui/README.md`
- `plan/adr_001_execution_tracker.md`

## Historical / status-snapshot docs

These should be read as dated snapshots unless updated explicitly.

- `plan/archive/phd2_stepwise_plan.md`
- `plan/archive/index_checklist.md`
- `plan/archive/step6_13_delta_generation_and_text_reviewers.md`
- `plan/archive/step6_13_implementation_notes.md`
- `plan/archive/document_glossary.md`
- `plan/archive/comments_inventory.md`

## Rule

If a document conflicts with the current runtime truth set above, trust the current runtime truth set and mark the conflicting doc as target-state, planning, or historical.
