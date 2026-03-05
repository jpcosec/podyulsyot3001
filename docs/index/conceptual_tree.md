# Conceptual Documentation Tree

This tree is the "design map" used to keep documentation coherent and low-drift.

## Tree

```text
PhD 2.0 Docs
├── Philosophy (why)
│   ├── project_overview
│   ├── structure_and_rationale
│   ├── execution_taxonomy_abstract
│   └── template_problem_statement
├── Graph (what runs)
│   ├── graph_definition
│   └── node_io_matrix
├── Templates (how to implement)
│   ├── node_template_discipline
│   ├── taxonomy_template_catalog
│   ├── llm templates
│   └── prompts
├── Business rules (what is allowed)
│   ├── claim_admissibility_and_policy
│   ├── sync_json_md
│   └── feedback_memory
├── Reference (contracts and glossary)
│   ├── artifact_schemas
│   └── document_glossary
├── Operations (how to run)
│   ├── tool_interaction_and_known_issues
│   └── non_llm_recovery_demo
└── Plan (how rollout is sequenced)
    ├── phd2_stepwise_plan
    ├── index_checklist
    └── template/README
```

## Ownership rule

- Each concept should have one canonical home.
- Cross-folder documents should link to canonical docs instead of repeating policy text.
- Historical aliases may exist temporarily but must not receive new substantive content.

## Drift prevention rule

Before editing documentation:

1. Identify the concept branch first.
2. Edit only the canonical document for that branch.
3. Update links/index if navigation changed.
4. Record major structure updates in `changelog.md`.
