#plan_docs Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

All issue-fixing work must stay aligned with `plan_docs/` and `docs/`.

---

## Working rule for every issue

Once an issue is solved, the next step is always:

1. Check whether any existing test is no longer valid and delete it if needed.
2. Add new tests where necessary.
3. Run the relevant tests.
4. Update `changelog.md`.
5. Delete the solved issue from both this index and the corresponding file in `plan_docs/issues/`.
6. Make a commit that clearly states what was fixed, making sure all required files are staged.

---

## Priority roadmap

### Phase 1 - Gaps (Quick Fixes)

| # | Issue | Status |
|---|-------|--------|
| GAP-01 | Unknown Nodes Rendering | ✅ Resolved |
| GAP-02 | Group Nodes Missing Visual Styling | ✅ Resolved |
| GAP-03 | Edge Relation Types Not Visible | ✅ Resolved |

All issues resolved! 🎉
