# Live Portal Extraction Is Broken On Real DOM

**Explanation:** Running `python -m src.automation.main scrape --source <portal> --limit 5` against live XING, StepStone, and TU Berlin pages produces 0 ingested jobs. This is not primarily a `JobPosting` schema-tightness problem. The evidence points to stale or broken real-page extraction:
1. Recent live logs show missing core fields such as `job_title`, plus `company_name`, `location`, and `employment_type` on multiple portals.
2. Older persisted artifacts prove the canonical `JobPosting` model can validate successfully when extraction returns even moderately complete data.
3. Current portal schemas under `src/automation/motors/crawl4ai/schemas/*.json` are likely no longer matching the live DOM.
4. `_normalize_payload()` can only repair partial payloads; it cannot recover when the extractor never captures the core fields in the first place.

This means the base problem is extractor drift on live portals, not just over-strict validation. It also means the current pipeline needs a clearer stage boundary between raw extraction and canonical normalization so partially-correct real data can be cleaned before strict validation.

**Reference:**
- `src/automation/motors/crawl4ai/scrape_engine.py` — `_extract_payload()`, `_normalize_payload()`, `_validate_payload()`
- `src/automation/motors/crawl4ai/schemas/xing_schema.json`
- `src/automation/motors/crawl4ai/schemas/stepstone_schema.json`
- `src/automation/motors/crawl4ai/schemas/tuberlin_schema.json`
- `src/automation/ariadne/models.py` — `JobPosting`
- `logs/automation/scrape_xing_20260409_122943.log`
- `logs/automation/scrape_stepstone_20260409_122959.log`
- `logs/automation/scrape_tuberlin_20260409_123020.log`

**Live evidence collected so far:**
- **XING**: `data/jobs/xing/149819348/nodes/ingest/failed/raw_extracted.json` shows CSS extraction returns only partial scalars; `data/jobs/xing/149819348/nodes/ingest/failed/content.md` shows the real job body is present under bold headings like `**Die Stelle im Überblick**` and `**Danach suchen wir**`, which require normalization/text mining rather than stricter selectors alone.
- **StepStone**: `data/jobs/stepstone/13785989/nodes/ingest/failed/raw_extracted.json` shows CSS extraction already captures rich responsibilities/requirements but leaves `company_name` and `employment_type` empty; `data/jobs/stepstone/13785989/nodes/ingest/failed/content.md` contains company, location, contract type, and remote policy in the hero block, so the failure is mainly scalar recovery/normalization, not body extraction.
- **TU Berlin**: `data/jobs/tuberlin/202258/nodes/ingest/failed/raw_extracted.json` shows CSS extraction captures `job_title`, `company_name`, `location`, and `reference_number`, but responsibilities are empty; `data/jobs/tuberlin/202258/nodes/ingest/failed/content.md` uses prose under `## Your responsibility` instead of bullet lists, so current normalization misses a valid responsibility block because it expects bulletized sections.

**Current diagnosis by portal:**
- **XING** — mixed extractor drift plus portal-specific heading normalization gap.
- **StepStone** — list extraction is now good enough to ingest, but scalar normalization is still over-broad on some postings and can pick the wrong company/location from surrounding hero or intro content.
- **TU Berlin** — prose-section normalization was the main gap; live ingest now works after treating `Your responsibility` prose as a valid responsibility block.

**What to fix:** Real portal scraping must reliably extract enough live-page data to build valid `JobPosting` objects for all supported portals without relying on mocks. This parent issue is now atomized into portal-specific remaining work so each live portal problem can be resolved independently.

**How to do it:**
1. Track remaining XING work in `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md`.
2. Track remaining StepStone scalar scoping work in `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md`.
3. Keep shared extraction-level diagnostics in place so portal-specific fixes stay evidence-based.
4. Coordinate with `plan_docs/issues/gaps/extraction-and-canonical-normalization-are-not-explicitly-separated.md` so extraction repair and normalization-stage design do not get mixed together.

**Depends on:** `plan_docs/issues/gaps/xing-live-extraction-remains-unstable.md`, `plan_docs/issues/gaps/stepstone-scalar-normalization-still-overmatches.md`
