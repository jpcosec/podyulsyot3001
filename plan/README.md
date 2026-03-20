# Planning Tree

`plan/` is for planning only.

Use this area for:

- active implementation plans
- migration plans
- ADRs and execution trackers
- reusable planning templates
- archived planning snapshots when they still matter

Do not use `plan/` as current runtime truth.

## Planning structure

- `plan/adr/` - architecture decisions
- `plan/runtime/` - backend/runtime migration and target-state planning
- `plan/ui/` - workbench/sandbox/UI planning
- `plan/template/` - reusable planning templates and planning rules
- `plan/archive/` - historical planning snapshots worth retaining

Heavy implementation detail should usually live near code, with `plan/` linking to it when needed.

## Required plan shape

Every substantial plan should be tree-shaped, not just sequential.

Minimum sections:

1. context
2. objective
3. dependency tree of steps
4. impact/dependency tree of code under change
5. libraries and tools involved
6. implementation approach or pseudocode
7. examples/templates to imitate
8. done definition
9. what not to do
10. how to test
11. docs/changelog updates required
12. commit boundary per step

## Required step policy

Each step should end with:

- a test or verification action
- a documentation/changelog check
- a commit
- optional user review gate

## Start here

- `plan/template/planning_dependency_tree_template.md`
- `plan/adr_001_execution_tracker.md`
