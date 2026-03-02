# Incremental Pipeline Fix

Three surgical fixes to the application pipeline. Each fix is independently valuable — the pipeline keeps working between each change.

**Problem statement:** The current pipeline produces generic motivation letters because:
1. The scraper over-filters job postings, losing context that matters for personalization
2. The 3-agent matching pipeline (Matcher→Seller→Checker) runs without human feedback, producing thin/wrong mappings
3. The motivation letter only sees filtered scraps, never the full job description

**Approach:** Fix the data flow, not the architecture. No new frameworks, no grand rewrites.

## Plan Files

1. `01-fix-scraping.md` — Stop filtering data the LLM needs
2. `02-fix-matching.md` — Replace 3-agent gauntlet with single match + human review
3. `03-fix-motivation.md` — Feed full context to motivation letter generation

## Implementation Order

Fix 1 → Fix 2 → Fix 3 (each builds on the previous, but each is independently shippable)

## What stays untouched

- `src/render/` — deterministic renderers work fine
- `src/models/` — Pydantic contracts stay (we extend, not replace)
- `src/utils/gemini.py` — LLM transport works fine
- `src/prompts/` — prompts get edited, not restructured
- ATS evaluation — separate concern, not broken
