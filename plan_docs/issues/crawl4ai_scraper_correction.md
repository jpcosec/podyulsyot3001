# Crawl4AI Scraper Correction Plan

## Goal

Bring `src/scraper/` back in line with Crawl4AI's intended design and fix the current source-modeling mistake where some sources, especially XING, try to recover listing-only fields from detail pages.

The immediate correction is not to pass the full listing page forward. Instead, for each job we should persist and forward only the listing fragment that belongs to that job, plus normalized listing metadata derived from that fragment.

## Working Principle

The source onboarding policy remains:

1. use LLM-assisted extraction when adding a new source quickly
2. stabilize extraction with representative samples
3. persist deterministic schemas
4. make saved schemas the default runtime path
5. keep LLM extraction only as fallback or temporary bootstrap support

## Current Problems

1. `posted_date` for XING is treated as if it belonged to the detail page, but in practice it is exposed more reliably in listing cards
2. the scraper currently persists the full listing page for every job, but it does not isolate the one teaser/card that corresponds to the target job
3. relative listing dates like `5 days ago` are preserved without anchoring them to the scrape timestamp, so they are incomplete evidence
4. `src/scraper/smart_adapter.py` uses a custom LiteLLM rescue path instead of `LLMExtractionStrategy`
5. schema generation has been treated as a generic fix for missing source modeling
6. generated schemas are based on too little representative variation
7. ingestion counts fetched pages even when validation fails

## Target Architecture

### Stage 1: Separate listing and detail extraction contracts

For sources that need it, introduce two explicit extraction layers:

- listing extraction
- detail extraction

Expected shape for XING:

- listing: `url`, `job_id`, listing teaser/card HTML, listing teaser text, `posted_date`, teaser metadata when useful
- detail: responsibilities, requirements, company data, rich description
- merge: combine job-specific listing payload + detail payload before `JobPosting` validation

Acceptance criteria:

- `posted_date` can be sourced from listing without guessing from detail
- validation runs only after the merged payload is built

### Stage 2: Add job-scoped listing artifacts

For every discovered job, persist only the listing fragment that corresponds to that job in addition to the full listing page kept for debugging.

This requires changing the discovery contract. Today adapters effectively return URLs. After the refactor, discovery should return structured `DiscoveryEntry` objects instead, carrying at least the job URL plus listing-side teaser data.

Recommended direction:

- replace `extract_links(...) -> list[str]` with discovery extraction that returns structured entries
- use Crawl4AI extraction on the listing page itself where possible, instead of ad-hoc regex-only link discovery
- include the teaser/card HTML or enough structured information to reconstruct the job-scoped listing fragment deterministically

Target per-job artifacts under `nodes/ingest/proposed/`:

- `listing_case.html` — raw HTML fragment for the matching teaser/card
- `listing_case.cleaned.html` — cleaned HTML fragment for the matching teaser/card
- `listing_case.md` — text/markdown extracted only from that teaser/card
- `listing_case.json` — normalized listing metadata for this job only

`listing_case.json` should contain, when available:

- `job_id`
- `url`
- `search_url`
- `listing_position`
- `scraped_at`
- `listed_at_relative`
- `listed_at_iso`
- teaser title/company/location/salary/employment data
- `teaser_text`

Contract note:

- `scraped_at` should become part of the normalized ingest evidence for every source
- downstream stages should prefer `listed_at_iso` when available over raw relative strings like `5 days ago`

Acceptance criteria:

- no downstream stage needs to inspect the full listing page to understand one job
- the job payload carries only its own listing evidence, not neighboring jobs
- relative date text is always anchored by `scraped_at`

### Stage 3: Replace manual LLM rescue with Crawl4AI-native LLM extraction

Remove the custom LiteLLM extraction path in `src/scraper/smart_adapter.py`.

Replace it with `LLMExtractionStrategy` inside `CrawlerRunConfig` for fallback extraction.

Acceptance criteria:

- no direct LiteLLM rescue logic remains in adapters
- fallback extraction uses Crawl4AI's `input_format`, chunking, and usage reporting

### Stage 4: Regenerate schemas from representative samples

Adopt multi-sample schema generation for unstable sources.

For each problematic source:

- capture several representative detail pages
- include layout variants
- regenerate deterministic schemas from those samples

Acceptance criteria:

- schema generation uses representative samples, not a single lucky page
- generated schemas avoid teaser/sticky/similar-job selectors

### Stage 5: Add source-specific extraction composition where required

Some sources will need source-specific merge logic.

For XING specifically:

- extract the correct teaser/card fragment from discovery results
- normalize listing-side metadata from that fragment
- derive an anchored absolute listing date using the scrape timestamp
- attach the job-scoped listing payload to the detail fetch
- merge before validation and persistence

After XING, replicate the same pattern to other sources even if they do not need it immediately, so all sources expose a uniform ingest surface.

Acceptance criteria:

- XING ingested jobs carry real `posted_date` values when available in listing
- detail extraction no longer tries to hallucinate listing-only fields
- other sources also produce job-scoped `listing_case.*` artifacts for consistency

### Stage 6: Make ingestion fail closed

Refine ingestion result handling so a fetch is not counted as a successful ingested job unless validation passed.

This should happen early in the rollout so CLI runs immediately reflect the true health of the refactor.

Acceptance criteria:

- CLI success counts reflect validated ingestions only
- failed validations still persist diagnostics, but not as successful ingests

### Stage 7: Test and lock the pattern

Add tests around:

- listing + detail merge behavior
- job-scoped listing fragment extraction
- relative-date normalization against scrape timestamp
- fallback extraction through `LLMExtractionStrategy`
- ingestion success counting
- representative-source behavior for XING

Acceptance criteria:

- scraper behavior is covered at the architectural seams, not only with happy-path smoke tests

## Execution Order

1. add job-scoped `listing_case.*` artifacts to the ingest contract
2. normalize relative listing dates with `scraped_at`
3. harden ingest success accounting so failures stop being counted as successful ingests
4. introduce listing/detail merge support in the scraper base
5. refactor XING to use listing-case metadata for `posted_date`
6. replicate job-scoped listing artifacts for the other sources
7. replace manual LLM rescue with `LLMExtractionStrategy`
8. regenerate schemas from representative samples
9. update README, contracts, and tests

## Notes

- Do not relax the contract to hide extraction mistakes.
- Do not patch source-specific gaps by making prompts looser.
- The fix is better source modeling plus Crawl4AI-native strategy usage.
- Full listing pages remain useful debug artifacts, but they are not the payload to pass forward for a single job.
