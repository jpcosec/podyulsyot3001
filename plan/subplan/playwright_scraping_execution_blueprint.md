# Playwright-Centered Scraping Execution Blueprint

## Goal

Define the concrete implementation shape for a Playwright-capable scraping subsystem that:

- preserves raw HTML + provenance as JSON-first artifacts
- keeps `src/nodes/scrape/logic.py` thin
- supports listing crawl/search orchestration outside the semantic graph
- leaves room for controlled auto-postulation as a separate bounded capability

This blueprint is execution-focused and complements `plan/subplan/json_first_scraping_subsystem_migration.md`.

## Non-Negotiable Constraints

- `src/core/` stays deterministic and framework-safe for node logic boundaries.
- Downstream nodes only depend on canonical scrape output (`raw_text` + stable metadata), not fetch internals.
- Graph control-plane state remains small; heavy payloads live on disk artifacts.
- Every scrape run persists provenance and replay evidence.
- Auto-postulation is opt-in, source-allowlisted, and separately audited.

## Target Module Skeleton

```text
src/core/scraping/
  __init__.py
  service.py                    # facade used by nodes/CLI
  contracts.py                  # TypedDict/Pydantic for requests/results
  registry.py                   # adapter registration + resolve by source/domain

  adapters/
    __init__.py
    base.py                     # SourceAdapter protocol/base class
    generic.py                  # fallback adapter
    stepstone.py                # first concrete source adapter

  fetch/
    __init__.py
    base.py                     # Fetcher protocol
    http_fetcher.py             # fast default mode
    playwright_fetcher.py       # browser mode
    policy.py                   # escalation rules (http -> playwright)

  extract/
    __init__.py
    html_to_text.py             # baseline deterministic extraction
    quality.py                  # extraction quality gates

  normalize/
    __init__.py
    canonical.py                # source extraction -> canonical scrape JSON

  crawl/
    __init__.py
    listing.py                  # listing traversal/discovery
    dedup.py                    # known/new id resolution

  persistence/
    __init__.py
    artifact_store.py           # bridge to WorkspaceManager + ArtifactWriter

  policy/
    __init__.py
    compliance.py               # domain allowlist, apply allowlist, delays
```

## Public API (Facade)

`src/core/scraping/service.py` exposes only these operations:

```python
def scrape_detail(request: ScrapeDetailRequest) -> ScrapeDetailResult
def crawl_listing(request: CrawlListingRequest) -> CrawlListingResult
```

### ScrapeDetailRequest

- `source: str`
- `source_url: str`
- `job_id: str | None`
- `preferred_fetch_mode: Literal["http", "playwright", "auto"] = "auto"`
- `run_id: str | None`

### ScrapeDetailResult

- `canonical_scrape: dict[str, Any]`
- `artifact_refs: dict[str, str]`
- `warnings: list[str]`
- `used_fetch_mode: Literal["http", "playwright"]`

### CrawlListingRequest

- `source: str`
- `listing_url: str`
- `known_ids: list[str]`
- `max_pages: int`
- `run_id: str | None`

### CrawlListingResult

- `discovered_urls: list[str]`
- `discovered_ids: list[str]`
- `new_ids: list[str]`
- `artifact_refs: dict[str, str]`
- `warnings: list[str]`

## Artifact Contract (JSON-First)

All artifacts live under `data/jobs/<source>/<job_id>/nodes/scrape/`.

### Detail Scrape Artifacts

- `input/fetch_metadata.json`
  - requested URL, resolved URL, timestamp, adapter key/version, retry count, fetch mode, timings, status flags
- `input/raw_snapshot.json`
  - raw HTML reference or inline payload hash + length + encoding hints
- `proposed/source_extraction.json`
  - source-specific extraction output (title/body/sections/warnings/provenance)
- `approved/canonical_scrape.json`
  - stable payload for downstream nodes

Optional:

- `meta/quality_report.json`
  - extraction quality checks and pass/fail reasons

### Canonical Scrape JSON (minimum)

- `source`
- `source_url`
- `resolved_url`
- `job_id`
- `raw_text`
- `original_language`
- `warnings`
- `artifact_refs`

## Node Integration Contract

`src/nodes/scrape/logic.py` becomes a thin adapter:

1. Build `ScrapeDetailRequest` from graph state.
2. Call `scrape_detail(...)`.
3. Map result to existing `IngestedData` shape.
4. Attach artifact refs in metadata.

No source-specific parsing, selector logic, or fetch branching remains in node logic.

## Crawl/Search Orchestration Boundary

Keep crawl/search orchestration outside prep-match semantic flow.

Recommended boundary:

- `src/cli/run_available_jobs.py` (or dedicated crawl CLI) calls `crawl_listing(...)`
- per discovered URL -> enqueue/start per-job prep run
- semantic graph still starts at `scrape` for each job

This avoids polluting graph state with listing traversal details.

## Auto-Postulation Boundary

Auto-postulation must be a separate subsystem and disabled by default.

Guardrails:

- source allowlist (`supports_apply=true`)
- explicit operator approval artifact before submit
- dry-run mode default
- submission evidence artifact required
- fail-stop on captcha/MFA/manual-only states

Suggested path (later phase):

- `src/core/application/` with adapter-style source handlers
- consume canonical scrape + generated artifacts, not raw browser internals from scrape node

## Phase Plan

### Phase A - Skeleton + Contracts

- Create `src/core/scraping/` module tree.
- Add facade contracts and no-op implementations.
- Add first adapter registration path (`generic`, `stepstone`).

Acceptance:

- import paths stable
- facade callable from tests

### Phase B - Fetch Layer + Persistence

- Implement `http_fetcher`, `playwright_fetcher`, and escalation policy.
- Implement artifact store bridge using existing `WorkspaceManager` + `ArtifactWriter`.
- Persist `fetch_metadata.json` + `raw_snapshot.json`.

Acceptance:

- both fetch modes covered by tests
- artifact files written deterministically

### Phase C - Extraction + Canonical Normalization

- Implement deterministic HTML-to-text extraction.
- Implement quality gates (`too_short`, likely cookie wall, low signal ratio).
- Implement canonical normalization and write `source_extraction.json` + `canonical_scrape.json`.

Acceptance:

- canonical payload backward-compatible with `IngestedData` use
- quality failures are fail-closed with explicit error context

### Phase D - Node Rewire

- Refactor `src/nodes/scrape/logic.py` to facade call.
- Keep output keys expected by translate/extract nodes.
- Update scrape tests to patch facade, not internals.

Acceptance:

- prep-match path works unchanged downstream
- no direct fetch/parsing code left in node

### Phase E - Listing Crawl Orchestration

- Implement `crawl_listing(...)` and crawl artifact writing.
- Integrate with batch CLI flow for discover -> run.

Acceptance:

- discovered/new IDs deterministic
- listing metadata trail persisted

### Phase F - Auto-Postulation (Optional, Separate)

- Create isolated `core/application` contracts.
- Enforce approval + allowlist controls.
- Add submission evidence artifact model.

Acceptance:

- dry-run complete
- one source pilot with explicit operator gate

## Test Matrix

- Unit: adapter resolution, fetch policy fallback, extraction quality gates, canonical schema fields
- Integration: detail scrape end-to-end artifacts, scrape node facade integration
- Regression: `translate_if_needed` and `extract_understand` unchanged behavior with new scrape output
- CLI: listing crawl orchestration produces stable discovered/new IDs
- Safety: auto-postulation blocked when approval artifact missing

## Copy/Skip Map from Postulator3000

Copy pattern only:

- adapter registry shape
- fetch strategy separation
- page-model/extraction isolation concept

Skip for now:

- recorder/generator subsystems
- broad marketplace/product metadata tiers
- heavy DB-bound raw model persistence in scraper runtime

## Definition of Done

- `src/nodes/scrape/logic.py` is thin and source-agnostic
- all scrape artifacts persisted as JSON-first trail
- downstream prep-match nodes run without interface break
- listing crawl orchestration runs outside semantic graph
- optional auto-postulation remains isolated and policy-gated
