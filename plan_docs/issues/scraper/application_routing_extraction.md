# Application Routing Extraction

**Why deferred:** The scraper should preserve raw evidence now, but robustly inferring how to apply often requires a later interpretation stage rather than deterministic scrape-time extraction.
**Last reviewed:** 2026-03-29

## Problem / Motivation

Some postings ask candidates to apply by email, others send them to a company portal, and others rely on third-party application flows. The current scraper contract now has fields for this information, but the extraction strategy is not mature enough to treat these fields as reliably scrape-time, source-agnostic facts.

Trying to force this into the scraper layer risks brittle heuristics and false certainty.

## Proposed Direction

Keep preserving the raw evidence in the ingest layer:

- detail HTML and markdown
- listing-case artifacts
- links and apply targets when obvious

Then add a later interpretation/enrichment step that determines:

- `application_method`
- `application_url`
- `application_email`
- `application_instructions`

That step can combine source-specific heuristics with LLM interpretation when needed.

## Linked TODOs

- `src/scraper/models.py` — `# TODO(future): validate whether application routing belongs in scrape-time contract or a later interpretation step — see plan_docs/issues/scraper/application_routing_extraction.md`
