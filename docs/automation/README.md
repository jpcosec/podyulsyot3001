# Automation System

The `src/automation/` package is the runtime home for all browser automation: job discovery (scraping) and job application. It replaced the old split between `src/scraper/` and `src/apply/` in the 2026-04-06 Phase 1 migration.

## Documents in this folder

- `docs/automation/architecture.md` — design rationale, Ariadne boundary, motor separation, data flows
- `docs/automation/` ← you are here

## Implementation references

- `src/automation/README.md` — package layout, boundary rules, CLI usage, how to extend, troubleshooting
- `src/automation/ariadne/models.py` — Ariadne portal schema and canonical semantic models
- `src/automation/portals/` — portal intent files (one per portal per operation)
- `src/automation/motors/crawl4ai/` — Crawl4AI motor (scrape engine, apply engine, portal translators)
- `src/automation/motors/browseros/cli/` — BrowserOS CLI motor (MCP client, executor, backend)
- `src/automation/main.py` — unified CLI (`scrape` / `apply` subcommands)

## External library references

- `docs/reference/external_libs/browseros/readme.txt` — BrowserOS reference intro and index
- `docs/reference/external_libs/crawl4ai/readme.txt` — Crawl4AI reference intro and index

Discovery runs may expand beyond the aggregator portal itself: when a posting resolves to an external ATS or careers `application_url`, the Crawl4AI scrape engine can launch a company-domain discovery pass and ingest additional openings under a dedicated `company-<domain>` source namespace.

## Standards that apply

- `docs/standards/code/basic.md` — error contracts, LogTag, docstrings
- `docs/standards/code/crawl4ai_usage.md` — Crawl4AI bootstrap and schema convergence rules
- `docs/standards/code/ingestion_layer.md` — boundary validation rules for scrape-time inputs
