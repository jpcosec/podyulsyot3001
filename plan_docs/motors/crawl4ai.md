# Crawl4AI Motor — Current State

Date: 2026-04-04

## What Crawl4AI actually does today

Crawl4AI serves two distinct roles in this codebase. Both run through the same
library but use it in fundamentally different ways.

### Role 1: Page fetcher and structured extractor (scraping)

Base class: `SmartScraperAdapter` in `src/scraper/smart_adapter.py`

**Two execution modes:**

- **Discovery** (`run()`): listing page fetch → link extraction → batch `arun_many()`
  on detail pages → per-job structured extraction → artifact persistence
- **Single fetch** (`fetch_job()`): one URL → `arun()` → extract → persist

**Extraction lifecycle (two-tier, deterministic-first):**

1. **CSS schema** via `JsonCssExtractionStrategy` — loads cached schema from
   `data/ariadne/assets/crawl4ai_schemas/<source>_schema.json`. If no cache exists
   and an LLM key is available, generates one from a sample page using
   `JsonCssExtractionStrategy.generate_schema()` and caches it.
2. **LLM rescue** — if CSS extraction fails `JobPosting` validation, falls back to
   `litellm.acompletion()` on the page markdown.

**Known anti-pattern:** the LLM rescue calls litellm directly instead of using
`LLMExtractionStrategy` inside Crawl4AI. This contradicts the project standard in
`docs/standards/code/crawl4ai_usage.md`.

**What portal adapters provide for scraping:**

- `source_name` — portal identifier
- `supported_params` — CLI filter names
- `get_search_url()` — listing URL builder
- `extract_job_id()` — stable job ID from URL
- `extract_links()` — discovery entries from listing crawl result
- `get_llm_instructions()` — portal-specific extraction hints
- `get_schema_generation_hints()` — hints for CSS schema generation

**Crawl4AI configuration used:**

- `BrowserConfig`: headless, text-mode (no images)
- `CrawlerRunConfig`: bypass cache, simulate user, magic mode, word count threshold,
  excluded tags (nav, footer, script, style, aside)
- `SemaphoreDispatcher`: max 5 concurrent sessions, rate limiter on 429/503

**Artifacts produced** (per job, under `data/jobs/<source>/<job_id>/nodes/ingest/proposed/`):

- `content.md` — detail page markdown
- `raw_page.html` — detail page raw HTML
- `cleaned_page.html` — detail page cleaned HTML
- `raw_extracted.json` — raw structured extraction output
- `listing.json` — listing-side context
- `listing_content.md`, `listing_page.html`, `listing_page.cleaned.html` — full listing surfaces
- `listing_case.json`, `listing_case.md`, `listing_case.html`, `listing_case.cleaned.html` — job-scoped listing context
- `scrape_meta.json` — validation/result metadata
- `state.json` — validated `JobPosting` payload (or merged partial payload on failure)

### Role 2: Browser automation engine (applying)

Base class: `ApplyAdapter` in `src/apply/smart_adapter.py`

**Single execution flow:**

1. Navigate to job page + open apply modal (C4A-Script)
2. Validate CSS selectors against live DOM (JS `page.evaluate()` via hook)
3. Fill form fields + upload files in a single `arun()` call
4. (dry-run stops here)
5. Submit + verify success text

**How it uses Crawl4AI:**

- `CrawlerRunConfig` with `c4a_script` for page interaction sequences
  (open modal, fill form, submit — each is a separate C4A-Script string)
- `wait_for` with CSS selectors for synchronization between phases
- `hooks` (`before_retrieve_html`) for raw Playwright calls —
  `page.set_input_files()` for file uploads (no C4A-Script equivalent),
  `page.evaluate()` for DOM validation
- `BrowserConfig` with `user_data_dir` for persistent session cookies
- `screenshot=True` for pre-submit and post-submit evidence
- `session_id` for session continuity across multiple `arun()` calls
- `js_only=True` for in-session calls that don't need navigation

**What portal adapters provide for applying:**

- `get_form_selectors()` — `FormSelectors` (CSS selectors for all form elements)
- `get_open_modal_script()` — C4A-Script to click apply button + wait for modal
- `get_fill_form_script(profile)` — C4A-Script with `{{placeholder}}` template syntax
- `get_submit_script()` — C4A-Script for the submit action
- `get_success_text()` — text fragment expected in confirmation page
- `get_session_profile_dir()` — persistent browser profile path
- `_get_portal_base_url()` — used by `setup_session()` for initial manual login

**Artifacts produced** (per job, under `data/jobs/<source>/<job_id>/nodes/apply/`):

- `proposed/application_record.json` — filled fields, CV path, submitted_at
- `proposed/screenshot.png` — state just before submit
- `proposed/screenshot_submitted.png` — state after submit (auto mode only)
- `proposed/error_state.png` — written only on exception
- `meta/apply_meta.json` — status, timestamp, error

## Capabilities summary

| Capability | Scraping | Applying |
|---|---|---|
| Page fetching | Yes (listing + detail) | Yes (navigate to job page) |
| Structured extraction | Yes (CSS schema + LLM rescue) | No |
| C4A-Script interaction | No (pages fetched as-is) | Yes (multi-phase scripts) |
| DOM querying/validation | No | Yes (JS evaluate via hooks) |
| File upload | No | Yes (Playwright `set_input_files`) |
| Session persistence | No (stateless, text-mode) | Yes (persistent profile dir) |
| Screenshots | No | Yes (pre/post-submit) |
| Batch execution | Yes (`arun_many` + dispatcher) | No (single job per run) |
| Rate limiting | Yes (SemaphoreDispatcher) | No |

## Crawl4AI features used vs available

**Used today:**

- `AsyncWebCrawler`, `arun()`, `arun_many()`
- `BrowserConfig` (headless, text_mode, user_data_dir, persistent context)
- `CrawlerRunConfig` (cache_mode, extraction_strategy, c4a_script, js_only,
  wait_for, session_id, screenshot, hooks, simulate_user, magic, override_navigator)
- `JsonCssExtractionStrategy` + `generate_schema()`
- `SemaphoreDispatcher`, `RateLimiter`
- `LLMConfig` (for schema generation only — rescue uses litellm directly)

**Available but not used:**

- `LLMExtractionStrategy` (should replace direct litellm rescue)
- `JsonXPathExtractionStrategy`, `RegexExtractionStrategy`
- Full C4A-Script DSL for scraping (currently only used in apply)
- `CacheMode` options beyond BYPASS
- Multiple extraction strategies per run
- Crawl4AI-native chunking and usage reporting for LLM extraction

## Existing documentation

- Scraper README: `src/scraper/README.md`
- Apply README: `src/apply/README.md`
- Crawl4AI usage standard: `docs/standards/code/crawl4ai_usage.md`
- Crawl4AI external reference: `docs/reference/external_libs/crawl4ai/readme.txt`

## Known gaps between docs and code

1. **LLM rescue anti-pattern**: `_llm_rescue()` calls litellm directly, violating
   `crawl4ai_usage.md` which requires `LLMExtractionStrategy`.
2. **Motor description undersells capabilities**: the plan docs describe Crawl4AI as
   "execution and extraction logic" but it's both an observation backend (fetch +
   extract) and an action backend (navigate, fill, click, upload, submit).
3. **Schema cache location**: documented as temporary in `asset_placement.md` but
   code still hardcodes `data/ariadne/assets/crawl4ai_schemas/`.
