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
- Added the remaining architectural issue for Ariadne ownership of canonical normalization. The live portal extraction backlog is now resolved on current XING, StepStone, and TU Berlin runs.

## Roots

- `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md`

## Parallelizable groups

- Depth 0: `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md`

## Blockers

- `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md` blocks semantic ownership because canonical job cleanup lives in a motor implementation instead of the neutral Ariadne layer.

## Dependency graph

- `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md` -> no dependencies

## Current indexed issues

1. `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md`
   - Scope: Move canonical job normalization ownership into Ariadne or an adjacent neutral semantic layer instead of leaving it in Crawl4AI motor code
   - Depends on: none
   - Expected outputs: Clear Ariadne ownership boundary, semantic-layer normalization module, backend-neutral tests, Ariadne-owned `raw`/`cleaned`/`extracted` contract
