# StepStone Live BrowserOS Rescue Still Misreads Some Detail Pages

**Explanation:** After fixing the narrower StepStone location misclassification rule, a fresh broader live StepStone sample exposed a different defect: some StepStone pages still fail because BrowserOS rescue misreads the page title or swaps company/location when the live page shape degrades or is interrupted.

Examples from live artifacts:
- `data/jobs/stepstone/13808297/nodes/ingest/failed/cleaned.json` shows `location` extracted as `NTT DATA` and `company_name` left `null`
- `data/jobs/stepstone/13815025/nodes/ingest/failed/cleaned.json` shows `job_title` extracted as `Your connection was interrupted`

This is a different failure class than the earlier hero-location bug.

**Reference:**
- `src/automation/ariadne/job_normalization.py`
- `data/jobs/stepstone/13808297/nodes/ingest/failed/cleaned.json`
- `data/jobs/stepstone/13815025/nodes/ingest/failed/cleaned.json`
- `docs/automation/live_scrape_coverage.md`

**What to fix:** Make StepStone rescue more robust against degraded or interrupted detail pages so company and title extraction do not accept obviously bad page states.

**How to do it:**
1. Detect degraded/interrupted StepStone page states before semantic extraction proceeds.
2. Add guards so company/location/title extraction rejects obvious page-error content.
3. Re-run broader StepStone live coverage and confirm the misread variants either ingest correctly or fail with explicit degraded-page diagnostics.

**Depends on:** none
