# XING Live Coverage Is Not Broad Enough

**Explanation:** XING has been validated on current live scrape pages, but the evidence still covers too few page variants to establish a reliable confidence envelope for the portal.

**Reference:**
- `data/jobs/xing/`
- `src/automation/motors/crawl4ai/scrape_engine.py`

**What to fix:** Validate XING across multiple live posting variants and document which XING page shapes are stable versus heuristic-sensitive.

**How to do it:**
1. Select multiple live XING postings across different employers/templates.
2. Re-run scrape validation and compare artifacts.
3. Record stable versus unstable XING variants.
4. Add artifact-based regression coverage where useful.

**Depends on:** none
