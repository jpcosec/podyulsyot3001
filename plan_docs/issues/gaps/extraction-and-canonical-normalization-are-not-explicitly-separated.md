# Extraction And Canonical Normalization Are Not Explicitly Separated

**Explanation:** The scrape pipeline currently blurs two different responsibilities:
1. raw extraction from unstable, portal-specific page data
2. normalization into the canonical `JobPosting` contract

That makes failures harder to reason about. Real artifacts now show cases where extraction is partially successful but still contains portal garbage or unstable shapes, for example wrapped payloads, teaser-style locations like `Berlin + 0 more`, and section headings that need semantic cleanup before canonical validation. When extraction and normalization are mixed together, the next step sees half-cleaned data and it becomes unclear whether the root cause is stale selectors, poor rescue output, or insufficient normalization.

The pipeline needs an explicit stage boundary and explicit output artifacts:
- Stage 1: preserve the raw portal payload exactly as extracted (`raw`)
- Stage 2: normalize and clean that payload into a canonical intermediate (`cleaned`)
- Stage 3: validate and emit the final canonical extraction (`extracted`)

The expected output contract should be visible in both code and artifacts:
- `raw`: source-shaped payload with no semantic cleanup
- `cleaned`: normalized intermediate with cleanup/backfills/section mining applied
- `extracted`: final validated `JobPosting` payload

This keeps the canonical contract strict while acknowledging that extraction from real portals is noisy and sometimes faulty.

**Reference:**
- `src/automation/motors/crawl4ai/scrape_engine.py` — `_extract_payload()`, `_parse_payload()`, `_normalize_payload()`, `_validate_payload()`
- `src/automation/ariadne/models.py` — `JobPosting`
- `data/jobs/xing/149819348/nodes/ingest/failed/raw_extracted.json`
- `data/jobs/xing/149819348/nodes/ingest/failed/content.md`
- `data/jobs/xing/149819348/nodes/ingest/failed/state.json`
- `data/jobs/stepstone/13785989/nodes/ingest/failed/raw_extracted.json`
- `data/jobs/stepstone/13785989/nodes/ingest/failed/content.md`
- `data/jobs/stepstone/13785989/nodes/ingest/failed/state.json`
- `data/jobs/tuberlin/202258/nodes/ingest/failed/raw_extracted.json`
- `data/jobs/tuberlin/202258/nodes/ingest/failed/content.md`
- `data/jobs/tuberlin/202258/nodes/ingest/failed/state.json`

**Observed normalization cases from live data:**
- **XING**: extraction yields partial structured data, while the real body uses bold headings and teaser-flavored values like `Berlin + 0 more` that should be cleaned before validation.
- **StepStone**: extraction already yields strong list fields, but scalar normalization is delicate: some postings leave hero scalars empty while others cause over-matching into descriptive text or navigation noise. This argues for a dedicated scalar normalization pass with stronger scope boundaries before validation.
- **TU Berlin**: extraction captures some scalars but misses responsibilities because the page expresses them as prose under `## Your responsibility` instead of bullet lists. This argues for normalization that can convert prose sections into canonical list fields.

**What to fix:** Introduce an explicit normalization step and output contract between raw extraction and canonical validation. The system should preserve separate `raw`, `cleaned`, and `extracted` outputs, where the normalizer cleans portal noise and partial extraction artifacts without weakening the final `JobPosting` contract.

**How to do it:**
1. Define a dedicated intermediate payload model or documented dict shape for post-extraction, pre-validation cleanup.
2. Preserve and persist three distinct outputs: `raw`, `cleaned`, and `extracted`.
3. Move portal cleanup logic into an explicit normalization phase that runs after CSS/BrowserOS/LLM extraction but before `JobPosting` validation.
4. Capture normalization diagnostics showing which values came from raw extraction, listing-case backfill, BrowserOS rescue, hero-block mining, or text mining.
5. Add normalization rules for known real-data garbage and shape mismatches, such as wrapped payloads, bold section headings, teaser-derived location suffixes, empty scalar strings, list-item shape cleanup, and prose-only responsibility sections.
6. Validate the final canonical object only after normalization is complete.

**Depends on:** none
