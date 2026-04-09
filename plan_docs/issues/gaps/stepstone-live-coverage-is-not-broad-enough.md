# StepStone Live Coverage Is Not Broad Enough

**Explanation:** StepStone is currently ingesting on tested live pages, but the evidence still covers too few live variants to define the real confidence envelope for that portal.

**Reference:**
- `data/jobs/stepstone/`
- `src/automation/motors/crawl4ai/scrape_engine.py`

**What to fix:** Validate StepStone across multiple live posting variants and document which StepStone page shapes are stable versus heuristic-sensitive.

**How to do it:**
1. Select multiple live StepStone postings across different employers/templates.
2. Re-run scrape validation and compare artifacts.
3. Record stable versus unstable StepStone variants.
4. Add artifact-based regression coverage where useful.

**Depends on:** none
