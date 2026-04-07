# Discovery Entry Contract

## Explanation

Per-job listing evidence is still inconsistent across sources. Discovery is not yet uniformly modeled as structured entries carrying listing metadata and job-scoped artifacts.

## Reference in src

- `src/automation/motors/crawl4ai/scrape_engine.py`
- `src/automation/motors/crawl4ai/portals/stepstone/scrape.py`
- `src/automation/motors/crawl4ai/portals/xing/scrape.py`

## What to fix

Make every source discovery path return structured discovery entries with enough listing-side context to produce reliable `listing_case.*` artifacts.

## How to do it

Replace plain URL discovery outputs with typed entries containing URL, job ID, listing position, teaser text, and any source-specific metadata needed for deterministic merge behavior.

## Does it depend on another issue?

No.
