# StepStone Scalar Normalization Still Overmatches

**Explanation:** StepStone now ingests on live data, but scalar normalization can still overmatch into surrounding descriptive or navigation content. Recent live artifacts show `company_name` and `location` can be recovered from the wrong scope even when the page validates.

**Reference:**
- `src/automation/motors/crawl4ai/scrape_engine.py`
- `data/jobs/stepstone/13792824/nodes/ingest/proposed/state.json`
- `data/jobs/stepstone/13785989/nodes/ingest/proposed/state.json`

**What to fix:** Restrict StepStone scalar recovery so `company_name`, `location`, and related hero values come only from the true job hero block rather than surrounding description or navigation content.

**How to do it:**
1. Compare a correct and incorrect StepStone artifact side by side.
2. Add stronger scope rules for hero scalar extraction.
3. Re-run live StepStone scrapes across multiple postings and confirm stable scalar quality.

**Depends on:** none
