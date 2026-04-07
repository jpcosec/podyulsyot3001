# Postulator 3001 Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

All issue-fixing work must stay aligned with the rest of `plan_docs/` and `docs/`, with special care for `docs/standards/` so implementation, tests, and documentation remain consistent with the project's rules.

┄┄ Working rule for every issue

Once an issue is solved, the next step is always:

 1. Check whether any existing test is no longer valid and delete it if needed.
 2. Add new tests where necessary.
 3. Run the relevant tests.
 4. Update `changelog.md`.
 5. Delete the solved issue from both this index and the corresponding file in `future_docs/issues/`.
 6. Make a commit that clearly states what was fixed, making sure all required files are staged.

┄┄ Priority roadmap

┄┄┄ Phase 1 — [Phase name]

 1. `future_docs/issues/[path]/issue-name.md`
 2. `future_docs/issues/[path]/issue-name.md`

    • [Parallelization note if applicable]

┄┄┄ Phase 2 — [Phase name]

 3. `future_docs/issues/[path]/issue-name.md`
    • depends on `future_docs/issues/[path]/issue-name.md`

    • [Parallelization note if applicable]

┄┄ Dependency summary

• `future_docs/issues/.../downstream.md`  ->  `future_docs/issues/.../upstream.md`

┄┄ Parallelization map

Phase 1  [1][2]          ← [note]
Phase 2     [3]          ← [note]
