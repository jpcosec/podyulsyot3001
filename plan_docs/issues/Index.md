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
- Extraction and normalization issues are resolved on the currently tested live scrape pages.
- Remaining issues now cover backend-specific live apply validation, broader live portal coverage, BrowserOS `/chat` runtime confidence, and a narrower StepStone live location normalization defect discovered during broader StepStone coverage sampling. Broader XING live coverage is now resolved for the current sampled envelope.

## Roots

- `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md`
- `plan_docs/issues/gaps/live-portal-coverage-is-not-broad-enough.md`
- `plan_docs/issues/gaps/browseros-chat-agent-surface-is-not-fully-validated-for-runtime-use.md`
- `plan_docs/issues/gaps/browseros-live-apply-backend-is-not-validated.md`
- `plan_docs/issues/gaps/crawl4ai-live-apply-backend-is-not-validated.md`
- `plan_docs/issues/gaps/tuberlin-live-coverage-is-not-broad-enough.md`
- `plan_docs/issues/gaps/browseros-chat-runtime-reliability-is-not-validated.md`
- `plan_docs/issues/gaps/stepstone-live-location-normalization-still-misclassifies-hero-metadata.md`

## Parallelizable groups

- Depth 0: `plan_docs/issues/gaps/browseros-live-apply-backend-is-not-validated.md`, `plan_docs/issues/gaps/crawl4ai-live-apply-backend-is-not-validated.md`, `plan_docs/issues/gaps/tuberlin-live-coverage-is-not-broad-enough.md`, `plan_docs/issues/gaps/browseros-chat-runtime-reliability-is-not-validated.md`, `plan_docs/issues/gaps/stepstone-live-location-normalization-still-misclassifies-hero-metadata.md`
- Depth 1: `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md`, `plan_docs/issues/gaps/live-portal-coverage-is-not-broad-enough.md`, `plan_docs/issues/gaps/browseros-chat-agent-surface-is-not-fully-validated-for-runtime-use.md`
- Depth 2: `plan_docs/issues/gaps/browseros-chat-agent-surface-is-not-fully-validated-for-runtime-use.md`

## Blockers

- `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md` blocks confidence in real end-to-end application behavior because scrape validation does not prove live apply correctness.
- `plan_docs/issues/gaps/live-portal-coverage-is-not-broad-enough.md` blocks confidence across portal/page variants because current live scrape validation is still narrow.
- `plan_docs/issues/gaps/browseros-chat-agent-surface-is-not-fully-validated-for-runtime-use.md` blocks confidence in workflows that still depend on BrowserOS `/chat` beyond MCP-first scrape rescue.
- `plan_docs/issues/gaps/stepstone-live-location-normalization-still-misclassifies-hero-metadata.md` blocks full StepStone confidence because some live hero layouts still fill `location` with contract metadata.

## Dependency graph

- `plan_docs/issues/gaps/browseros-live-apply-backend-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/crawl4ai-live-apply-backend-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md` -> `plan_docs/issues/gaps/browseros-live-apply-backend-is-not-validated.md`, `plan_docs/issues/gaps/crawl4ai-live-apply-backend-is-not-validated.md`
- `plan_docs/issues/gaps/tuberlin-live-coverage-is-not-broad-enough.md` -> no dependencies
- `plan_docs/issues/gaps/live-portal-coverage-is-not-broad-enough.md` -> `plan_docs/issues/gaps/tuberlin-live-coverage-is-not-broad-enough.md`
- `plan_docs/issues/gaps/browseros-chat-runtime-reliability-is-not-validated.md` -> no dependencies
- `plan_docs/issues/gaps/browseros-chat-agent-surface-is-not-fully-validated-for-runtime-use.md` -> `plan_docs/issues/gaps/browseros-chat-runtime-reliability-is-not-validated.md`
- `plan_docs/issues/gaps/stepstone-live-location-normalization-still-misclassifies-hero-metadata.md` -> no dependencies

## Current indexed issues

1. `plan_docs/issues/gaps/live-apply-flows-are-not-fully-validated.md`
   - Scope: Parent issue for live apply validation after child tasks define the matrix and validate each backend
   - Depends on: `plan_docs/issues/gaps/browseros-live-apply-backend-is-not-validated.md`, `plan_docs/issues/gaps/crawl4ai-live-apply-backend-is-not-validated.md`
   - Expected outputs: Working live apply matrix, backend-specific evidence, updated docs/routing assumptions

2. `plan_docs/issues/gaps/live-portal-coverage-is-not-broad-enough.md`
   - Scope: Parent issue for broader live scrape coverage after each portal variant set is validated independently
   - Depends on: `plan_docs/issues/gaps/tuberlin-live-coverage-is-not-broad-enough.md`
   - Expected outputs: Broader live portal evidence, variant coverage notes, regression artifacts/tests

3. `plan_docs/issues/gaps/browseros-chat-agent-surface-is-not-fully-validated-for-runtime-use.md`
   - Scope: Parent issue for `/chat` runtime confidence after dependency inventory and runtime validation are completed
   - Depends on: `plan_docs/issues/gaps/browseros-chat-runtime-reliability-is-not-validated.md`
   - Expected outputs: `/chat` support statement by workflow, validated runtime evidence, updated docs/contracts

4. `plan_docs/issues/gaps/browseros-live-apply-backend-is-not-validated.md`
   - Scope: Validate BrowserOS-backed live apply flows against the matrix
   - Depends on: none
   - Expected outputs: BrowserOS live apply evidence and support status by portal

5. `plan_docs/issues/gaps/crawl4ai-live-apply-backend-is-not-validated.md`
   - Scope: Validate Crawl4AI-backed live apply flows against the matrix
   - Depends on: none
   - Expected outputs: Crawl4AI live apply evidence and support status by portal

6. `plan_docs/issues/gaps/tuberlin-live-coverage-is-not-broad-enough.md`
   - Scope: Validate more TU Berlin live scrape variants
   - Depends on: none
   - Expected outputs: TU Berlin variant coverage notes and regression artifacts/tests

7. `plan_docs/issues/gaps/browseros-chat-runtime-reliability-is-not-validated.md`
   - Scope: Validate `/chat` runtime behavior for the workflows that still intentionally use it
   - Depends on: none
   - Expected outputs: Runtime evidence and support classification for `/chat` workflows

8. `plan_docs/issues/gaps/stepstone-live-location-normalization-still-misclassifies-hero-metadata.md`
   - Scope: Fix remaining StepStone live location misclassification on broader hero layouts
   - Depends on: none
   - Expected outputs: Correct StepStone location extraction across the broader sampled layouts
