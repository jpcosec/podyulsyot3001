# Cross Portal Discovery

## Explanation

Aggregator jobs often link to company ATS portals with more openings, but the pipeline does not yet follow those application URLs to discover additional roles.

## Reference in src

- `src/automation/main.py`
- `src/automation/motors/crawl4ai/scrape_engine.py`

## What to fix

Add a company-portal discovery pass that starts from known `application_url` targets and expands into additional job pages on the same ATS or careers domain.

## How to do it

Use Crawl4AI domain-scoped discovery with ATS-aware URL filtering, persist discovered jobs under a company-domain source contract, and connect the output back into the normal ingest pipeline.

## Does it depend on another issue?

Yes — `plan_docs/issues/unimplemented/application-routing-enrichment.md`.
