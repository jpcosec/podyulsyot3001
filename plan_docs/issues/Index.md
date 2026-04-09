# Postulator Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

---

## Working Rule For Every Issue

Once an issue is solved:

1. Check whether any existing test is no longer valid.
2. Add new tests where necessary.
3. Run the relevant tests.
4. Update `changelog.md`.
5. Delete the solved issue from both this index and the corresponding file in `plan_docs/issues/`.
6. Make a commit that clearly states what was fixed.

---

## Current State

The active and full test suites are healthy and the current operator/runtime docs are aligned with the codebase.

---

## Priority Roadmap

- [ ] **#5, #7 HITL Review Screens Redesign** — Replace existing `ReviewScreen` with four stage-specific screens and fix the submit bug. See `plan_docs/issues/gaps/hitl_review_screens.md`.
- [ ] **#3, #4, #6, #8, #9 Review UI Bugs and Refactors** — Address smaller bugs, dead code, and misalignments in the `review_ui` and its connection to the LangGraph API. See `plan_docs/issues/gaps/review_ui_bugs_and_refactors.md`.

---

## Dependency Summary

- No remaining indexed dependencies.

---

## Parallelization Map

- No remaining indexed phases.
