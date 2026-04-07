# XING Listing Metadata Composition

## Explanation

XING still lacks complete listing-side composition. Job payloads do not yet carry the full anchored listing evidence needed for fields such as `posted_date` and related teaser metadata.

## Reference in src

- `src/automation/motors/crawl4ai/portals/xing/scrape.py`
- `src/automation/motors/crawl4ai/scrape_engine.py`

## What to fix

Build the XING payload from job-scoped listing evidence plus detail-page extraction before final validation.

## How to do it

Extract and persist the matching teaser/card fragment, anchor relative dates with `scraped_at`, merge listing and detail payloads before validation, and add source-specific tests around the merge.

## Does it depend on another issue?

Yes — `plan_docs/issues/gaps/discovery-entry-contract.md`.
