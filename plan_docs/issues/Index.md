# unified-automation Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

All issue-fixing work must stay aligned with the rest of plan_docs/ and docs/, with special care for STANDARDS.md so implementation, tests, and documentation remain consistent with the project's rules.

## Initialization Procedure (Before Execution)

Before executing any issue or assigning work to a subagent, you MUST perform this ritual:
  1. Atomize: break down work into the smallest possible units.
  2. See what's redundant > merge.
  3. Legacy > delete.
  4. Contradictory > resolve.
  5. Iterate until the plan is clean and straightforward.
  6. Update `plan_docs/issues/Index.md`.
  7. Execute using the smallest possible/available subagent for each step. Provide the subagent with explicit context (e.g., architectural boundaries, limits, or relevant reference files) to prevent them from making wrong choices. Review their work.

## Working rule for every issue

Once an issue is solved, the next step is always:

  1. Check whether any existing test is no longer valid and delete it if needed.
  2. Add new tests where necessary.
  3. Run the relevant tests.
  4. Update changelog.md.
  5. Delete the solved issue from both this index and the corresponding file in plan_docs/issues/.
  6. Make a commit that clearly states what was fixed, making sure all required files are staged.

## Phase Completion Ritual

When all parallelizable issues in a given Phase/Level are completed, you MUST perform a compliance check before moving to the next Phase:
  1. Verify compliance: Check that the combined implementations of the phase comply with all project standards and architectural boundaries.
  2. Run all architectural fitness functions and full test suites to ensure no regressions were introduced.

## Priority roadmap

*No active issues. Index cleared after each phase completion.*

## Parallelization map

*Empty - ready for new issues.*