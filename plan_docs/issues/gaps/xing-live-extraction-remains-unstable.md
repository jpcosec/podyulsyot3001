# XING Live Extraction Remains Unstable

**Explanation:** StepStone and TU Berlin now ingest on real data after normalization improvements, but XING still remains unstable across live runs. The remaining failures mix two concerns: extraction drift on XING-specific content patterns and intermittent navigation/network instability before detail extraction completes.

**Reference:**
- `src/automation/motors/crawl4ai/scrape_engine.py`
- `src/automation/motors/crawl4ai/schemas/xing_schema.json`
- `data/jobs/xing/149819348/nodes/ingest/failed/`
- `logs/automation/`

**What to fix:** Make XING live scrape runs reliably produce valid `JobPosting` objects on current live pages, with stable detail fetch and correct normalization of XING-specific sections and teaser values.

**How to do it:**
1. Stabilize XING listing/detail navigation and capture a fresh failing artifact bundle when it breaks.
2. Tighten XING-specific normalization rules using fresh live artifacts.
3. Validate repeated live XING runs until the portal ingests reliably.

**Depends on:** none
