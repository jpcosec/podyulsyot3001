# Crawl4AI Live Apply Backend Is Not Validated

**Explanation:** The Crawl4AI backend remains part of the apply system, but its live end-to-end behavior has not been validated on real authenticated apply flows under the same discipline used for scrape validation.

**Reference:**
- `src/automation/motors/crawl4ai/apply_engine.py`
- `src/automation/main.py`
- `tests/integration/test_live_apply.py`

**What to fix:** Validate the Crawl4AI apply backend on real supported portals according to the defined live validation matrix and record the result for each tested path.

**How to do it:**
1. Use the live apply validation matrix as the scope boundary.
2. Run Crawl4AI-backed dry-run apply validations on each in-scope portal.
3. Persist evidence and outcomes.
4. Update docs or routing assumptions if live behavior differs from expectations.

**Depends on:** none
