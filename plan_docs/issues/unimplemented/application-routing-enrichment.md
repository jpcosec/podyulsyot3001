# Application Routing Enrichment

## Explanation

The system still cannot reliably derive `application_method`, `application_url`, `application_email`, or `application_instructions` from ingest evidence. Without that layer, apply orchestration does not know how a job should actually be submitted.

## Reference in src

- `src/automation/ariadne/models.py`
- `src/automation/motors/crawl4ai/scrape_engine.py`

## What to fix

Implement a post-ingest interpretation step that turns raw scrape evidence into a reliable application-routing contract.

## How to do it

Build a routing enrichment module that combines source heuristics with selective LLM interpretation, stores the resolved routing fields, and exposes confidence/diagnostic data for review.

## Does it depend on another issue?

No.
