# Worktree Planning Protocol

This protocol defines how planning and continuity are managed in this repository.

## Scope Rules

1. `docs/` contains only documentation for the current implemented state.
2. `plan/` contains planning, execution tracking, and next-step sequencing.
3. Runtime data is not tracked in git.
4. New implementation planning runs in a dedicated worktree whenever practical.

## Branch and Worktree Policy

1. This worktree/branch is the integration baseline.
2. Each major plan gets its own worktree and branch:
   - Branch naming: `plan/<topic>`
   - Worktree naming: `<repo>-<topic>`
3. The plan file for that effort lives under `plan/` and is owned by that worktree.
4. Merge back only after tracker status, tests, and changelog are updated.

## Session Continuity Protocol

Start of session (fixed order):

1. Read `plan/adr_001_execution_tracker.md`.
2. Read `plan/archive/index_checklist.md`.
3. Read `changelog.md` (latest date block only).
4. Read code-local dependency docs in touched modules.

End of session (required):

1. Update tracker progress in `plan/adr_001_execution_tracker.md`.
2. Update `plan/archive/index_checklist.md` if phase/state changed.
3. Append major changes to `changelog.md`.
4. Produce a structured handoff containing next task and blockers.
5. Run protocol gate: `python -m src.cli.check_repo_protocol`.

## Enforcement Layer

1. CI gate: `.github/workflows/repo-protocol.yml` runs protocol checks on push/PR.
2. Pre-commit gate: `.pre-commit-config.yaml` runs protocol checks before commit.
3. Pre-push clean-tree gate: requires `python -m src.cli.check_repo_protocol --require-clean-tree`.

This clean-tree gate enforces that local codebase changes are committed before push.

## Code-Adjacent Documentation Rule

Documentation that explains implementation details must live inside or next to the module it describes.

Examples:

- `src/interfaces/api/README.md`
- `apps/review-workbench/README.md`
- `src/DEPENDENCY_GRAPH.md`

## Test Planning Rule

Before edits, identify impacted dependency nodes and run tests mapped to those nodes.

Minimum requirement:

1. Unit tests for directly changed module.
2. Contract or integration tests for direct dependents.
3. Build/type checks for impacted app/package.

Use `src/DEPENDENCY_GRAPH.md` as the first-pass impact map.
