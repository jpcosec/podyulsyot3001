# StepStone Live Location Normalization Still Misclassifies Hero Metadata

**Explanation:** Broader StepStone live coverage confirmed that ingestion succeeds across multiple postings, but some real StepStone hero layouts still misclassify `location` as contract metadata such as `Feste Anstellung`.

This is now a narrower defect than the old scalar scoping issue: company extraction is improved, but location recovery still confuses employment metadata and location metadata on some postings.

**Reference:**
- `src/automation/motors/crawl4ai/scrape_engine.py`
- `data/jobs/stepstone/13867304/nodes/ingest/proposed/state.json`
- `data/jobs/stepstone/13495192/nodes/ingest/proposed/state.json`
- `docs/automation/live_scrape_coverage.md`

**What to fix:** Refine StepStone live location normalization so hero metadata distinguishes real locations from employment/contract labels across broader posting variants.

**How to do it:**
1. Compare the successful and misclassified StepStone hero layouts from live artifacts.
2. Tighten location extraction so contract labels like `Feste Anstellung` cannot populate `location`.
3. Re-run broader live StepStone coverage to confirm corrected location extraction.

**Depends on:** none
