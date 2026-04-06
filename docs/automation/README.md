# Automation System

The `src/automation/` package is the runtime home for all browser automation: job discovery (scraping) and job application. It replaced the old split between `src/scraper/` and `src/apply/` in the 2026-04-06 Phase 1 migration.

## Documents in this folder

- `docs/automation/architecture.md` — design rationale, Ariadne boundary, motor separation, data flows
- `docs/automation/` ← you are here

## Implementation references

- `src/automation/README.md` — package layout, boundary rules, CLI usage, how to extend, troubleshooting
- `src/automation/ariadne/portal_models.py` — Ariadne portal schema (canonical portal intent models)
- `src/automation/portals/` — portal intent files (one per portal per operation)
- `src/automation/motors/crawl4ai/` — Crawl4AI motor (scrape engine, apply engine, portal translators)
- `src/automation/motors/browseros/cli/` — BrowserOS CLI motor (MCP client, executor, backend)
- `src/automation/main.py` — unified CLI (`scrape` / `apply` subcommands)

## Standards that apply

- `docs/standards/code/basic.md` — error contracts, LogTag, docstrings
- `docs/standards/code/crawl4ai_usage.md` — Crawl4AI bootstrap and schema convergence rules
- `docs/standards/code/ingestion_layer.md` — boundary validation rules for scrape-time inputs
