# Playwright Scraping Blueprint

## Goal

Define the implementation shape for a Playwright-capable scraping subsystem that:

- preserves raw HTML and provenance as JSON-first artifacts
- keeps `src/nodes/scrape/logic.py` thin
- supports listing crawl orchestration outside the semantic graph
- leaves room for controlled auto-postulation as a separate bounded capability

This blueprint complements `plan/03_scrapper/json_first_scraping_migration.md`.

## Non-negotiable constraints

- `src/core/` stays deterministic at node boundaries.
- Downstream nodes depend on canonical scrape output, not fetch internals.
- Heavy scrape payloads live on disk artifacts.
- Every scrape run persists provenance and replay evidence.
- Auto-postulation remains opt-in and separately audited.

## Public facade

`src/core/scraping/service.py` exposes only:

```python
def scrape_detail(request: ScrapeDetailRequest) -> ScrapeDetailResult
def crawl_listing(request: CrawlListingRequest) -> CrawlListingResult
```

## Target module shape

```text
src/core/scraping/
  service.py
  contracts.py
  registry.py
  adapters/
  fetch/
  extract/
  normalize/
  crawl/
  persistence/
  policy/
```

## Artifact contract

Under `data/jobs/<source>/<job_id>/nodes/scrape/` persist at minimum:

- `input/fetch_metadata.json`
- `input/raw_snapshot.json`
- `proposed/source_extraction.json`
- `approved/canonical_scrape.json`

## Phase sequence

1. Skeleton and contracts.
2. Fetch layer and persistence.
3. Extraction and canonical normalization.
4. Scrape-node rewire.
5. Listing crawl orchestration.
6. Optional auto-postulation.

## Done definition

- Scraping runs through the core facade.
- Artifacts are persisted deterministically.
- Downstream prep-match behavior stays compatible.
