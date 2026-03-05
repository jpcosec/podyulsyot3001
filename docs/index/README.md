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

1. `docs/graph/graph_definition.md`
2. `docs/graph/node_io_matrix.md`
3. `docs/architecture/core_io_and_provenance_manager.md`

### 3) Implement nodes with consistent shape

1. `docs/templates/node_template_discipline.md`
2. `docs/templates/taxonomy_template_catalog.md`
3. `docs/templates/llm/README.md`
4. `docs/templates/prompts/README.md`

### 4) Validate policy and review gates

1. `docs/business_rules/claim_admissibility_and_policy.md`
2. `docs/business_rules/sync_json_md.md`
3. `docs/business_rules/feedback_memory.md`

### 5) Run and troubleshoot

1. `docs/operations/tool_interaction_and_known_issues.md`
2. `docs/operations/non_llm_recovery_demo.md`

## Migration note

Some legacy paths still exist as compatibility stubs under `docs/architecture/`, `docs/overview/`, and `docs/prompts/`.

When adding new content, always write to canonical paths listed above.
