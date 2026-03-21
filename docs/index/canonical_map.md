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
- `docs/policy/claim_admissibility_and_policy.md`

## Current UI sandbox docs

These are current for sandbox/workbench behavior, not for pipeline runtime truth.

- `docs/ui/node_editor_behavior_spec.md`
- `docs/ui/node_editor_customization_and_architecture.md`
- `docs/ui/node_editor_compliance_matrix.md`
- `apps/review-workbench/src/sandbox/README.md`

## Official specs and design references

These are official specs or design-intent docs. Each one should say clearly what is implemented today and what remains future/target-state.

- `docs/reference/graph_state_contract.md`
- `docs/reference/artifact_schemas.md`
- `docs/reference/node_template_discipline.md`
- `docs/reference/node_io_target_matrix.md`
- `docs/architecture/core_io_and_provenance_manager_spec.md`
- `docs/architecture/sync_json_md_spec.md`
- `docs/policy/claim_admissibility_and_policy.md`

## Active planning / migration docs

These are planning records, not runtime truth.

- `plan/index_checklist.md`
- `plan/01_ui/fase1_minimal_json_editor.md`
- `plan/01_ui/fase2_neo4j_knowledge_graph.md`
- `plan/02_langchain/fase1_llm_wrappers_y_structured_output.md`
- `plan/02_langchain/fase2_full_pipeline_rewrite.md`
- `plan/03_scrapper/playwright_scraping_blueprint.md`
- `plan/03_scrapper/json_first_scraping_migration.md`

## Rule

If a document conflicts with the current runtime truth set above, trust the current runtime truth set and mark the conflicting doc as target-state, planning, or historical.
