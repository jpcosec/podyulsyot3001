# Business Rules Docs

> Status note (2026-03-20): this folder mixes current enforceable behavior with target-state policy design. Do not assume every file here is fully implemented in runtime. For current operator/runtime truth, cross-check `docs/reference/data_management_actual_state.md`, `docs/graph/node_io_matrix.md`, and `docs/operations/tool_interaction_and_known_issues.md`.

This folder documents policy and review-governance intent for pipeline behavior.

## Contents

- `claim_admissibility_and_policy.md` - target-state policy direction; only partially enforced in current runtime
- `sync_json_md.md` - target-state review-surface sync service spec; reusable service not yet implemented
- `feedback_memory.md` - mixed current/target-state note on feedback persistence and future reuse
