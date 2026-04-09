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
- Added live-data extraction issues for stale real-page schemas, Ariadne ownership of canonical normalization, BrowserOS runtime reachability, and missing BrowserOS fallback. Failed-run artifact visibility and explicit extraction staging are now resolved in code.

## Roots

- `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md`
- `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md`
- `plan_docs/issues/gaps/browseros-runtime-is-not-reachable-and-endpoints-are-inconsistent.md`

## Parallelizable groups

- Depth 0: `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md`, `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md`, `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md`, `plan_docs/issues/gaps/browseros-runtime-is-not-reachable-and-endpoints-are-inconsistent.md`
- Depth 1: `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
- Depth 2: `plan_docs/issues/unimplemented/browseros-agent-schema-fallback.md`

## Blockers

- `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md` blocks fully reliable live portal scraping because XING still fails intermittently on real runs.
- `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md` blocks clean data quality on StepStone because scalar normalization still overmatches surrounding content on some live postings.
- `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md` is the umbrella portal extraction issue and remains open until the remaining portal-specific child issues are resolved.
- `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md` blocks semantic ownership because canonical job cleanup lives in a motor implementation instead of the neutral Ariadne layer.
- `plan_docs/issues/gaps/browseros-runtime-is-not-reachable-and-endpoints-are-inconsistent.md` blocks BrowserOS-backed schema fallback because the BrowserOS MCP runtime cannot currently be reached from this repo.

## Dependency graph

- `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md` -> no dependencies
- `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md` -> no dependencies
- `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md` -> `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md`, `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md`
- `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md` -> no dependencies
- `plan_docs/issues/gaps/browseros-runtime-is-not-reachable-and-endpoints-are-inconsistent.md` -> no dependencies
- `plan_docs/issues/unimplemented/browseros-agent-schema-fallback.md` -> `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`, `plan_docs/issues/gaps/browseros-runtime-is-not-reachable-and-endpoints-are-inconsistent.md`

## Current indexed issues

1. `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`
   - Scope: Track the remaining umbrella extraction problem across portals after child portal issues were atomized
   - Depends on: `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md`, `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md`
   - Expected outputs: All remaining live portal child issues resolved and repeated live scrapes stable

2. `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md`
   - Scope: Stabilize XING live scrape runs so they repeatedly ingest valid `JobPosting` objects
   - Depends on: none
   - Expected outputs: Stable live XING detail fetch, XING-specific normalization fixes, repeated successful live runs

3. `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md`
   - Scope: Restrict StepStone scalar recovery to the real hero block so company and location fields stay clean across postings
   - Depends on: none
   - Expected outputs: Clean StepStone company/location recovery on repeated live scrapes

4. `plan_docs/issues/gaps/browseros-runtime-is-not-reachable-and-endpoints-are-inconsistent.md`
   - Scope: Make BrowserOS runtime addressing consistent and verify MCP reachability from this repo
   - Depends on: none
   - Expected outputs: One canonical BrowserOS base URL, matching docs/code, successful runtime connectivity check

5. `plan_docs/issues/gaps/canonical-job-normalization-is-not-owned-by-ariadne.md`
   - Scope: Move canonical job normalization ownership into Ariadne or an adjacent neutral semantic layer instead of leaving it in Crawl4AI motor code
   - Depends on: none
   - Expected outputs: Clear Ariadne ownership boundary, semantic-layer normalization module, backend-neutral tests, Ariadne-owned `raw`/`cleaned`/`extracted` contract

6. `plan_docs/issues/unimplemented/browseros-agent-schema-fallback.md`
   - Scope: Add BrowserOS agent fallback to generate extraction schemas when CSS+LLM fail
   - Depends on: `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`, `plan_docs/issues/gaps/browseros-runtime-is-not-reachable-and-endpoints-are-inconsistent.md`
   - Expected outputs: SchemaGenerationFallback class, integration into extraction pipeline, tests
