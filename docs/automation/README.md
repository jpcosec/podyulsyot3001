# Automation System

The `src/automation/` package is the runtime home for all browser automation: job discovery (scraping) and job application. It replaced the old split between `src/scraper/` and `src/apply/` in the 2026-04-06 Phase 1 migration.

## Documents in this folder

- `docs/automation/architecture.md` — design rationale, Ariadne boundary, motor separation, data flows
- `docs/automation/` ← you are here

## Implementation references

- `src/automation/README.md` — package layout, boundary rules, CLI usage, how to extend, troubleshooting
- `src/automation/ariadne/models.py` — Ariadne portal schema and canonical semantic models
- `src/automation/portals/` — portal intent files (one per portal per operation)
- `src/automation/motors/crawl4ai/` — Crawl4AI motor executor
- `src/automation/motors/browseros/` — BrowserOS executor
- `src/automation/main.py` — unified CLI (`scrape` / `apply` subcommands)

## Authoritative architecture references

- `docs/ariadne/architecture_and_graph.md`
- `docs/ariadne/execution_interfaces.md`
- `docs/ariadne/recording_and_promotion.md`

Discovery runs may expand beyond the aggregator portal itself: when a posting resolves to an external ATS or careers `application_url`, the Crawl4AI scrape engine can launch a company-domain discovery pass and ingest additional openings under a dedicated `company-<domain>` source namespace.

## Standards that apply

- `STANDARDS.md` — canonical workflow, documentation, and code standards
- `AGENTS.md` — repository execution context and architecture pointers
