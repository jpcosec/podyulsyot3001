# Automation Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

## Working rule for every issue

Once an issue is solved:
1. Check whether any existing test is no longer valid.
2. Add new tests where necessary.
3. Run the relevant tests.
4. Update `changelog.md`.
5. Delete the solved issue from both this index and the corresponding file in `plan_docs/issues/`.
6. Make a commit that clearly states what was fixed.

## Legacy audit

- No indexed issue is currently marked for deletion instead of repair.
- The prior root-level `plan_docs/issues/index.md` and ad-hoc root issue file were replaced so the issue entrypoint now follows `docs/standards/issue_guide.md`.
- All currently indexed extraction and normalization issues have been resolved. The index is empty.
