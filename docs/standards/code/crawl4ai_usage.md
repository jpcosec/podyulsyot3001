# Crawl4AI Usage Standard

This document defines how this repository should use Crawl4AI in the scraper layer so we do not drift into ad-hoc extraction patterns again.

## Scope

Applies to `src/scraper/`, especially:

- `src/scraper/smart_adapter.py`
- `src/scraper/providers/`
- `scrapping_schemas/`

This is a project-level engineering standard, not a replacement for the upstream docs.

## Upstream References

- Quick start: <https://docs.crawl4ai.com/core/quickstart/>
- LLM-free extraction strategies: <https://docs.crawl4ai.com/extraction/no-llm-strategies/>
- LLM extraction strategies: <https://docs.crawl4ai.com/extraction/llm-strategies/>
- C4A-Script and page interaction: <https://docs.crawl4ai.com/core/c4a-script/>

Read those first when changing scraper architecture.

## Core Rule

Use Crawl4AI the way it is designed to be used:

- navigation and extraction are configured through `CrawlerRunConfig`
- deterministic extraction uses Crawl4AI extraction strategies
- LLM extraction uses `LLMExtractionStrategy`, not custom LiteLLM calls outside Crawl4AI
- interaction-heavy pages use Crawl4AI page interaction (`js_code`, `wait_for`, or C4A-Script) before extraction

Do not build a parallel extraction framework around Crawl4AI.

## Extraction Lifecycle for a New Source

Every new source follows this progression:

1. start with Crawl4AI-assisted extraction to get the source working quickly
2. learn the DOM and stabilize selectors across multiple real pages
3. persist a deterministic schema in `scrapping_schemas/<source>_schema.json`
4. switch the source to prefer the saved schema for steady-state extraction
5. keep LLM extraction only as a fallback or temporary bootstrap tool

The steady-state goal is always: saved schema first, LLM second.

## Required Architecture Pattern

### 1. Separate discovery/listing from detail extraction

If a source exposes some fields in the listing page and others in the detail page, model them as separate extraction boundaries.

Typical examples:

- listing page: `url`, `job_id`, `posted_date`, teaser salary
- detail page: `responsibilities`, `requirements`, company details

Merge listing + detail payloads before validating against `JobPosting`.

Do not expect one detail-page schema to recover fields that only exist reliably in listing cards.

### 2. Prefer deterministic extraction first

Use:

- `JsonCssExtractionStrategy`
- `JsonXPathExtractionStrategy`
- `RegexExtractionStrategy` when appropriate

The default approach for repetitive pages is LLM-free extraction.

### 3. Use LLM extraction through Crawl4AI only

When deterministic extraction is not enough, use `LLMExtractionStrategy` inside `CrawlerRunConfig`.

Do not:

- call LiteLLM directly from adapter code
- build custom chunking outside Crawl4AI
- manually recreate prompt/extraction plumbing already provided by the library

If we need LLM rescue, it must benefit from Crawl4AI's:

- `input_format`
- chunking
- usage reporting
- strategy integration
- consistent result handling

### 4. Generate schemas from multiple samples when the DOM varies

When generating a schema for a source with layout variation, use multiple representative HTML samples as described in the upstream docs.

Do not rely on a single sample for sites with:

- teaser cards plus detail page content
- repeated sticky headers
- mobile/desktop duplicates
- optional sections that shift element positions

The target is stable selectors, not positional selectors that happen to work once.

### 5. Use interaction tools when the DOM requires preparation

If the page requires expansion, clicking, scrolling, or dynamic hydration before extraction, use Crawl4AI interaction features:

- `js_code`
- `wait_for`
- C4A-Script when the flow is interaction-heavy or easier to express procedurally

Do not try to compensate for an unprepared DOM by making the extractor prompt more vague.

## Anti-Patterns

The following patterns are not acceptable:

- custom post-crawl LiteLLM extraction outside `LLMExtractionStrategy`
- treating schema generation as a substitute for source modeling
- using one detail-page schema to infer listing-only fields
- keeping extraction metadata only in transient logs instead of structured artifacts
- counting a fetch as a successful ingestion when `JobPosting` validation failed

## Expected Runtime Shape

For each source, the scraper should make these concerns explicit:

- listing/discovery extraction contract
- detail extraction contract
- merge step
- validation against `src/scraper/models.py`
- fallback policy
- saved deterministic schema(s)

## Review Checklist for Crawl4AI Changes

Before merging scraper changes, verify:

- extraction strategies live in `CrawlerRunConfig`
- any LLM usage goes through `LLMExtractionStrategy`
- schema generation uses representative samples for unstable DOMs
- listing-only fields are not being guessed from detail pages
- interaction-heavy pages use Crawl4AI interaction features instead of prompt hacks
- the module README in `src/scraper/README.md` still matches the implementation

## Current Design Direction

The intended long-term pattern for this repository is:

- new source bootstrap: LLM-assisted
- stable source operation: saved schema first
- fallback: Crawl4AI-native LLM extraction only when deterministic extraction fails

That is the standard going forward.
