# Representative Schema Samples

## Explanation

Schema generation is still too dependent on single samples. That makes selectors fragile and increases the chance of fitting one lucky page instead of the source's real layout variants.

## Reference in src

- `src/automation/motors/crawl4ai/scrape_engine.py`

## What to fix

Generate and validate deterministic schemas from representative sample sets rather than one example page.

## How to do it

Capture multiple detail pages per unstable source, regenerate schemas against that sample set, and add checks that exclude teaser or related-job selectors from the final schema.

## Does it depend on another issue?

No.
