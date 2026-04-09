# TU Berlin Live Coverage Is Not Broad Enough

**Explanation:** TU Berlin is currently ingesting on tested live pages, but the validation set is too narrow to establish confidence across the portal's likely content variants.

**Reference:**
- `data/jobs/tuberlin/`
- `src/automation/motors/crawl4ai/scrape_engine.py`

**What to fix:** Validate TU Berlin across multiple live posting variants and document which TU Berlin page shapes are stable versus heuristic-sensitive.

**How to do it:**
1. Select multiple live TU Berlin postings across available templates.
2. Re-run scrape validation and compare artifacts.
3. Record stable versus unstable TU Berlin variants.
4. Add artifact-based regression coverage where useful.

**Depends on:** none
