# Scraping Subsystem

This directory contains the current scraping runtime.

## Purpose

- detail scraping via `scrape_detail(...)`
- listing crawling via `crawl_listing(...)`
- source adapters, fetch policy, extraction, normalization, and artifact persistence

## Key files

- `service.py` - facade entrypoints and orchestration
- `registry.py` - source/adaptor registration
- `adapters/` - source-specific URL and listing helpers
- `strategies/` - source-specific extraction strategies
- `fetch/` - HTTP and Playwright fetchers
- `persistence/artifact_store.py` - scrape artifact writing

## Runtime contract

- writes JSON-first scrape artifacts under `nodes/scrape/`
- preserves `raw/source_text.md` for operator readability
- supports TU Berlin and StepStone-specific behavior in the current repo

## Central references

- `docs/reference/data_management_actual_state.md`
- `docs/graph/node_io_matrix.md`
- `plan/subplan/playwright_scraping_execution_blueprint.md`
