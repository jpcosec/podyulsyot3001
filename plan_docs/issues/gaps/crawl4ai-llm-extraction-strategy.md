# Crawl4AI LLM Extraction Strategy

## Explanation

Fallback extraction still uses direct LiteLLM calls instead of Crawl4AI's native `LLMExtractionStrategy`. That diverges from project standards and keeps extraction behavior split across two patterns.

## Reference in src

- `src/automation/motors/crawl4ai/scrape_engine.py`

## What to fix

Move fallback extraction onto Crawl4AI-native strategy wiring.

## How to do it

Replace manual completion calls with `LLMExtractionStrategy` in the active scraper path, keep the same schema/output contract, and add tests or fixtures that exercise the fallback path.

## Does it depend on another issue?

No.
