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
- The live scrape validation issue was executed and removed; it exposed one concrete shared runtime gap for real portal navigation.
- The shared live portal navigation blocker is resolved; real XING, StepStone, and TU Berlin pages now load with Crawl4AI's local browser, so the next shared runtime issue is extraction normalization.

## Roots

- `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`

## Parallelizable groups

- Depth 0: `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
- Depth 1: `plan_docs/issues/gaps/portal-live-routing-validation.md`
- Depth 2: `plan_docs/issues/gaps/portal-live-onsite-apply-validation.md`
- Depth 3: `plan_docs/issues/gaps/portal-live-validation-triage.md`, `plan_docs/issues/unimplemented/crawl4ai-persistent-profile-auth.md`, `plan_docs/issues/unimplemented/crawl4ai-browseros-session-import.md`, `plan_docs/issues/unimplemented/crawl4ai-env-secret-login.md`

## Blockers

- `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md` blocks the live routing pass because the real scrape pass still cannot produce valid ingest payloads.
- `plan_docs/issues/gaps/portal-live-routing-validation.md` blocks the onsite apply dry-run pass because only confirmed onsite routes should enter safe live apply validation.
- `plan_docs/issues/gaps/portal-live-onsite-apply-validation.md` and the earlier passes block triage because follow-up defects should be grounded in observed runtime behavior.
- `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md` also blocks the three Crawl4AI auth implementation tracks because they need stable real-portal ingestion and runtime behavior before auth validation can be trusted.

## Dependency graph

- `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md` -> no dependencies
- `plan_docs/issues/gaps/portal-live-routing-validation.md` -> `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
- `plan_docs/issues/gaps/portal-live-onsite-apply-validation.md` -> `plan_docs/issues/gaps/portal-live-routing-validation.md`
- `plan_docs/issues/gaps/portal-live-validation-triage.md` -> `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`, `plan_docs/issues/gaps/portal-live-routing-validation.md`, `plan_docs/issues/gaps/portal-live-onsite-apply-validation.md`
- `plan_docs/issues/unimplemented/crawl4ai-persistent-profile-auth.md` -> `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
- `plan_docs/issues/unimplemented/crawl4ai-browseros-session-import.md` -> `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
- `plan_docs/issues/unimplemented/crawl4ai-env-secret-login.md` -> `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`

## Current indexed issues

1. `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
   - Scope: normalize real portal extractor output into valid `JobPosting` payloads
   - Depends on: none
   - Expected outputs: successful ingestion where data is already sufficient, plus narrower follow-up issues where it is not
2. `plan_docs/issues/gaps/portal-live-routing-validation.md`
   - Scope: prove routing outcomes against live ingest payloads
   - Depends on: `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
   - Expected outputs: routing validation matrix and routing-specific follow-up issues where needed
3. `plan_docs/issues/gaps/portal-live-onsite-apply-validation.md`
   - Scope: prove safe live onsite apply dry-run behavior for supported apply portals
   - Depends on: `plan_docs/issues/gaps/portal-live-routing-validation.md`
   - Expected outputs: apply dry-run matrix and portal-specific replay/session follow-up issues where needed
4. `plan_docs/issues/gaps/portal-live-validation-triage.md`
   - Scope: convert live validation results into the next concrete issue backlog
   - Depends on: `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`, `plan_docs/issues/gaps/portal-live-routing-validation.md`, `plan_docs/issues/gaps/portal-live-onsite-apply-validation.md`
   - Expected outputs: follow-up issue files, cleaned index, and changelog update
5. `plan_docs/issues/unimplemented/crawl4ai-persistent-profile-auth.md`
   - Scope: make Crawl4AI reuse persistent authenticated browser profiles when credential metadata requests it
   - Depends on: `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
   - Expected outputs: runtime profile wiring, tests, and real-portal validation path
6. `plan_docs/issues/unimplemented/crawl4ai-browseros-session-import.md`
   - Scope: let BrowserOS-seeded authenticated sessions be handed off into Crawl4AI
   - Depends on: `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
   - Expected outputs: session import/export contract, implementation, and validation path
7. `plan_docs/issues/unimplemented/crawl4ai-env-secret-login.md`
   - Scope: let Crawl4AI execute direct env-secret login flows where a stable login form exists
   - Depends on: `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
   - Expected outputs: guarded login bootstrap, secret resolution wiring, and tests
