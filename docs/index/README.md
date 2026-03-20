# Documentation Index

This index is the entrypoint for documentation navigation.

Supporting index docs:

- Canonical map: `docs/index/canonical_map.md`
- Conceptual tree: `docs/index/conceptual_tree.md`
- Pruning plan: `docs/index/pruning_plan.md`

## Read this first

If you need to know what runs today, start with:

1. `README.md`
2. `docs/index/canonical_map.md`
3. `docs/graph/nodes_summary.md`
4. `docs/reference/data_management_actual_state.md`
5. `docs/operations/tool_interaction_and_known_issues.md`

Many architecture and plan docs in this repo are target-state or historical snapshots rather than current runtime truth.

## Canonical concept map

- Philosophy: `docs/philosophy/`
- Graph architecture: `docs/graph/`
- Templates: `docs/templates/`
- Business rules: `docs/business_rules/`
- Reference material: `docs/reference/`
- Operations: `docs/operations/`
- Implementation plan: `plan/`

## Architecture split

### Backend / runtime references

- `docs/architecture/core_io_and_provenance_manager.md`
- `docs/architecture/graph_state_contract.md`
- `docs/architecture/graph_reactivity_protocol.md`

### Frontend / sandbox references

- `docs/architecture/node_editor_behavior_spec.md`
- `docs/architecture/node_editor_customization_and_architecture.md`
- `docs/architecture/node_editor_compliance_matrix.md`
- `docs/UI_plan/README.md`

## Quick reading paths

### 1) Understand runtime graph behavior

1. `docs/graph/nodes_summary.md`
2. `docs/graph/node_io_matrix.md`
3. `docs/graph/match_review_cycle.md`
4. `docs/reference/data_management_actual_state.md`
5. `docs/architecture/core_io_and_provenance_manager.md`
6. `docs/operations/tool_interaction_and_known_issues.md`

### 2) Understand design intent and target-state architecture

1. `docs/philosophy/project_overview.md`
2. `docs/philosophy/structure_and_rationale.md`
3. `docs/architecture/graph_state_contract.md`
4. `docs/reference/artifact_schemas.md`
5. `docs/templates/node_template_discipline.md`

### 3) Understand the node editor sandbox

1. `docs/architecture/node_editor_behavior_spec.md`
2. `docs/architecture/node_editor_customization_and_architecture.md`
3. `docs/architecture/node_editor_compliance_matrix.md`
4. `docs/UI_plan/README.md`

### 4) Planning and migration work

1. `plan/subplan/deterministic_parity_migration_from_phd.md`
2. `plan/subplan/review_ui_and_flow_observability.md`
3. `plan/subplan/langchain_langgraph_adoption_evaluation.md`
4. `plan/adr_001_execution_tracker.md`

## Status rule

When a doc says what the system should do and another says what it currently does, prefer the current-runtime docs listed in `docs/index/canonical_map.md`.
