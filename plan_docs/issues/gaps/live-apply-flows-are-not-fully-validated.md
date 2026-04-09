# Live Apply Flows Are Not Fully Validated

**Explanation:** Scrape ingestion has now been validated on real XING, StepStone, and TU Berlin pages, but full apply flows have not been validated to the same level on real portals. The repository still lacks evidence that end-to-end apply behavior works reliably across the supported portal/backends matrix under live conditions.

This matters because scrape success does not prove that:
1. routing decisions remain correct on live apply URLs
2. Ariadne maps still match current live apply forms
3. BrowserOS and Crawl4AI apply backends behave correctly on real authenticated pages
4. dry-run and non-dry-run apply behavior are safe on live sites

**Reference:**
- `src/automation/main.py`
- `src/automation/portals/routing.py`
- `src/automation/portals/*/maps/`
- `src/automation/motors/browseros/`
- `src/automation/motors/crawl4ai/apply_engine.py`
- `tests/integration/test_live_apply.py`

**What to fix:** Validate live apply behavior end-to-end on real supported portals and record which backend/portal combinations are confirmed working, dry-run only, or still unsupported. This parent issue is atomized into matrix-definition and backend-specific validation tasks.

**How to do it:**
1. Define the validation matrix in `plan_docs/issues/unimplemented/live-apply-validation-matrix-is-not-defined.md`.
2. Validate the BrowserOS backend in `plan_docs/issues/gaps/browseros-live-apply-backend-is-not-validated.md`.
3. Validate the Crawl4AI backend in `plan_docs/issues/gaps/crawl4ai-live-apply-backend-is-not-validated.md`.
4. Fold resulting evidence back into docs and routing assumptions.

**Depends on:** `plan_docs/issues/gaps/browseros-live-apply-backend-is-not-validated.md`, `plan_docs/issues/gaps/crawl4ai-live-apply-backend-is-not-validated.md`
