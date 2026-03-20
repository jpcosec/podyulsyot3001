# Documentation Index

This index is the entrypoint for documentation navigation.

Supporting index docs:

- Canonical map: `docs/index/canonical_map.md`
- Conceptual tree: `docs/index/conceptual_tree.md`
- Pruning plan: `docs/index/pruning_plan.md`

This index should stay lightweight. It is for navigation, not for holding deep subsystem detail.

## Read this first

If you need to know what runs today, start with:

1. `README.md`
2. `docs/index/canonical_map.md`
3. `docs/runtime/graph_flow.md`
4. `docs/runtime/data_management.md`
5. `docs/operations/tool_interaction_and_known_issues.md`

## Current docs tree

- `docs/runtime/` - current runnable backend/runtime behavior
- `docs/policy/` - current policy/rule notes still relevant to runtime
- `docs/reference/` - stable current reference and pointers
- `docs/ui/` - current sandbox/workbench behavior docs
- `docs/operations/` - current operator playbooks
- `docs/index/` - navigation only

Anything primarily future-looking should live in `plan/`, not here.

## Quick reading paths

### 1) Understand runtime graph behavior

1. `docs/runtime/graph_flow.md`
2. `docs/runtime/node_io_matrix.md`
3. `docs/runtime/match_review_cycle.md`
4. `docs/runtime/data_management.md`
5. `docs/runtime/core_io_and_provenance.md`
6. `docs/operations/tool_interaction_and_known_issues.md`

### 2) Understand design intent and target-state architecture

1. `plan/archive/project_overview.md`
2. `plan/archive/structure_and_rationale.md`
3. `plan/runtime/graph_state_contract.md`
4. `plan/runtime/artifact_schemas.md`
5. `plan/runtime/node_template_discipline.md`

### 3) Understand the node editor sandbox

1. `docs/ui/node_editor_behavior_spec.md`
2. `docs/ui/node_editor_customization_and_architecture.md`
3. `docs/ui/node_editor_compliance_matrix.md`
4. `apps/review-workbench/src/sandbox/README.md`

### 4) Planning and migration work

1. `plan/subplan/deterministic_parity_migration_from_phd.md`
2. `plan/subplan/review_ui_and_flow_observability.md`
3. `plan/subplan/langchain_langgraph_adoption_evaluation.md`
4. `plan/adr_001_execution_tracker.md`

## Status rule

When a doc says what the system should do and another says what it currently does, prefer the current-runtime docs listed in `docs/index/canonical_map.md`.
