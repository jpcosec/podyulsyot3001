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

BrowserOS recording, normalization, and draft-path promotion are functional. The remaining BrowserOS work is now concentrated in six areas: stable runtime endpoint resolution, a shared promotion intermediate, Level 2 promotion hardening, Level 1 MCP promotion, path validation/confidence, and one end-to-end discovery-to-replay proof.

## Priority roadmap

### Phase 1 — Runtime foundation (blocks all downstream BrowserOS work)

1. `plan_docs/issues/gaps/browseros-runtime-endpoint-resolution.md`
   - Introduce one canonical BrowserOS endpoint resolution/config policy.
   - This is the root blocker for consistent MCP and `/chat` behavior.

### Phase 2 — Shared promotion model (blocks both Level 1 and Level 2 finish-up)

2. `plan_docs/issues/unimplemented/browseros-shared-promotion-intermediate.md`
   - Define one shared intermediate model for BrowserOS Level 1 and Level 2 recordings.
   - Depends on: `plan_docs/issues/gaps/browseros-runtime-endpoint-resolution.md`

### Phase 3 — Promotion hardening (parallelizable after Phase 2)

3. `plan_docs/issues/gaps/browseros-level2-promotion-hardening.md`
   - Make Level 2 promotion robust enough for realistic BrowserOS-discovered flows.
   - Depends on: `plan_docs/issues/unimplemented/browseros-shared-promotion-intermediate.md`
4. `plan_docs/issues/gaps/browseros-level1-mcp-promotion.md`
   - Promote deterministic MCP traces into draft Ariadne paths through the same shared model.
   - Depends on: `plan_docs/issues/unimplemented/browseros-shared-promotion-intermediate.md`

### Phase 4 — Acceptance and proof

5. `plan_docs/issues/gaps/browseros-path-validation-and-confidence.md`
   - Add explicit path validation/confidence before promoted BrowserOS paths are replay-eligible.
   - Depends on: `plan_docs/issues/gaps/browseros-level2-promotion-hardening.md`, `plan_docs/issues/gaps/browseros-level1-mcp-promotion.md`
6. `plan_docs/issues/unimplemented/browseros-discovery-to-replay-validation.md`
   - Prove one full BrowserOS discovery -> promotion -> deterministic replay flow end-to-end.
   - Depends on: `plan_docs/issues/gaps/browseros-path-validation-and-confidence.md`

### Phase 5 — Additional interface coverage (parallelizable with later phases once runtime is stable)

7. `plan_docs/issues/unimplemented/browseros-agent-interface-coverage.md`
   - Expand BrowserOS integration coverage for still-unused high-value MCP interfaces.
   - Depends on: `plan_docs/issues/gaps/browseros-runtime-endpoint-resolution.md`

## Dependency summary

Phase 1 -> Phase 2
Phase 2 -> Phase 3 [3][4]
Phase 3 -> Phase 4 [5] -> [6]
Phase 5 [7] is independent of Phases 3-4 once Phase 1 is done.

## Parallelization map

Phase 1 [1]
Phase 2 [2]
Phase 3 [3][4] - parallel
Phase 4 [5] then [6]
Phase 5 [7] - parallel with late Phase 3 or Phase 4 once [1] is done
