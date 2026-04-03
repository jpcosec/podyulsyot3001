# Scraper Fragility Issues

**Why deferred:** All four issues are non-blocking for current ingestion runs; addressing them requires provider-specific testing against live portals.
**Last reviewed:** 2026-03-29

## Problem / Motivation

Four independent fragility points were identified in the scraper layer during a review pass:

### 1. Module-level `PROVIDERS` instantiation (`main.py`)

`build_providers()` is called at import time (line 34), creating a `DataManager` at module load. This means any test or import of `src.scraper.main` triggers side effects (filesystem access). It also makes it impossible to pass a custom `DataManager` to the global registry without monkey-patching.

### 2. Naive `detect_language` fallback (`smart_adapter.py`)

Language detection relies on counting German marker words and umlauts. This fails silently on short postings, mixed-language headers, or job titles that happen to contain none of the markers. The result is written to `original_language` and influences downstream translation decisions.

### 3. `StepStoneAdapter.extract_links` returns plain URL strings

The StepStone adapter returns `list[str]` from `extract_links`, discarding per-card listing metadata (title, company, salary, employment type). The Xing adapter already returns rich `list[dict]` entries with `listing_data` and `listing_snippet`. StepStone should do the same to give the ingest layer full listing-case artifacts for each job.

### 4. Xing adapter relies on generated CSS class names

`XingAdapter._listing_data` uses the selector `span.marker-styles__Text-sc-8295785a-2` (a hashed/generated class name) to extract salary and employment type markers. Generated class names change with any frontend rebuild and will silently return empty data without any error or warning.

## Proposed Direction

1. **Import-time registry**: Move `PROVIDERS = build_providers()` inside `main()` or make it lazy. The `build_providers()` helper already accepts an optional `DataManager` — the fix is just call discipline.

2. **Language detection**: Replace the naive heuristic with a lightweight library (`langdetect` or `lingua`) on the markdown content. Alternatively, delegate to the LLM since language is already extracted by the rescue path and the LLM instructions already request `original_language`.

3. **StepStone listing metadata**: Implement `extract_links` to parse listing card HTML (similar to `XingAdapter`) and return `list[dict]` with `listing_data`, `listing_snippet`, and `listing_case_*` HTML surfaces.

4. **Xing class name selectors**: Replace the hardcoded generated class selector with structural heuristics (e.g. match text patterns for salary `€`/`TV-L` and employment-type tokens from the visible marker chips) or fall back to the LLM-extracted `listing_data` from the detail page.

## Linked TODOs

- `src/scraper/main.py:34` — `# TODO(future): PROVIDERS is built at import time — see plan_docs/issues/scraper/scraper_fragility.md`
- `src/scraper/smart_adapter.py` — `# TODO(future): detect_language is a naive heuristic, fails on short/mixed-language postings — see plan_docs/issues/scraper/scraper_fragility.md`
- `src/scraper/providers/stepstone/adapter.py` — `# TODO(future): extract_links returns plain strings, losing listing-side metadata — see plan_docs/issues/scraper/scraper_fragility.md`
- `src/scraper/providers/xing/adapter.py` — `# TODO(future): _listing_data uses generated CSS class names that break on portal rebuilds — see plan_docs/issues/scraper/scraper_fragility.md`
