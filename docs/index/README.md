# Documentation Index

This index is the entrypoint for the documentation architecture.

Use this folder to navigate by concept instead of by historical file location.

Supporting index docs:

- Canonical map: `docs/index/canonical_map.md`
- Conceptual tree: `docs/index/conceptual_tree.md`
- Pruning plan: `docs/index/pruning_plan.md`

## Canonical concept map

- Philosophy: `docs/philosophy/`
- Graph architecture: `docs/graph/`
- Templates (including prompts): `docs/templates/`
- Business rules: `docs/business_rules/`
- Reference material: `docs/reference/`
- Operations: `docs/operations/`
- Implementation plan: `plan/`

## Quick reading paths

### 1) Understand why the system exists

1. `docs/philosophy/project_overview.md`
2. `docs/philosophy/structure_and_rationale.md`
3. `docs/philosophy/execution_taxonomy_abstract.md`

### 2) Understand runtime graph behavior

1. `docs/graph/nodes_summary.md`
2. `docs/graph/node_io_matrix.md`
3. `docs/graph/match_review_cycle.md`
4. `docs/reference/data_management_actual_state.md`
5. `docs/architecture/core_io_and_provenance_manager.md`
6. `docs/architecture/graph_state_contract.md`

### 3) Implement nodes with consistent shape

1. `docs/templates/node_template_discipline.md`
2. `docs/templates/taxonomy_template_catalog.md`
3. `docs/templates/llm/README.md`
4. `docs/templates/prompts/README.md`
5. `docs/templates/prompts/prompt_anatomy_standard.md`
6. `docs/reference/contract_composition_framework.md`
7. `docs/reference/review_contract_case_decision_and_assistance.md`

### 4) Validate policy and review gates

1. `docs/business_rules/claim_admissibility_and_policy.md`
2. `docs/business_rules/sync_json_md.md`
3. `docs/business_rules/feedback_memory.md`
4. `docs/architecture/graph_reactivity_protocol.md`

### 5) Run and troubleshoot

1. `docs/operations/tool_interaction_and_known_issues.md`
2. `docs/operations/non_llm_recovery_demo.md`

## Migration note

Legacy compatibility stubs were removed.

When adding new content, always write to canonical paths listed above.
If you encounter an old path in notes or historical docs, map it via `docs/index/canonical_map.md`.
