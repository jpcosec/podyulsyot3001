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

## Current state

The BrowserOS roadmap tracked in this index is currently clean. Runtime endpoint resolution, Level 1 and Level 2 recording, shared promotion, path validation, interface coverage, and one low-load live discovery -> replay proof are all in place.

## Priority roadmap

No open BrowserOS issues are currently indexed here.

## Dependency summary

No outstanding indexed BrowserOS dependencies.

## Parallelization map

No outstanding indexed BrowserOS work.
