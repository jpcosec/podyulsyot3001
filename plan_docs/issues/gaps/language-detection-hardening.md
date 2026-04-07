# Language Detection Hardening

## Explanation

The scraper still uses a simple German-marker heuristic for fallback language detection. It fails on short, mixed-language, or sparse postings and can corrupt downstream translation decisions.

## Reference in src

- `src/automation/motors/crawl4ai/scrape_engine.py`

## What to fix

Replace the naive fallback with a more reliable language detector or a structured extraction path that reports language explicitly.

## How to do it

Prefer a lightweight detector such as `lingua` or `langdetect`, keep the heuristic only as a last resort, and add unit cases for short and mixed-language postings.

## Does it depend on another issue?

No.
