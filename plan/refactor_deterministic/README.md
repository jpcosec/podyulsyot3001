# Deterministic Rebuild Plan

This folder contains the step-by-step refactor plan approved for the deterministic rebuild.

Execution rule:
- Implement one step at a time.
- Run deterministic tests after each step.
- Do not preserve legacy runtime behavior except contracts, graph reference, and deterministic tools.

Plan index:
- `00_scope_and_survivors.md`
- `01_documentation_and_contract_preservation.md`
- `02_hard_deletion.md`
- `03_new_langgraph_skeleton.md`
- `04_incremental_reimplementation.md`
- `05_testing_policy.md`
- `06_tracking_and_governance.md`
