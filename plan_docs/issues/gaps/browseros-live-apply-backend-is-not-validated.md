# BrowserOS Live Apply Backend Is Not Validated

**Explanation:** The BrowserOS backend is part of the supported apply architecture, but it has not yet been validated end-to-end on real authenticated apply pages in a way that establishes which portal flows actually work.

**Reference:**
- `src/automation/motors/browseros/`
- `src/automation/main.py`
- `tests/integration/test_live_apply.py`

**What to fix:** Validate the BrowserOS apply backend on real supported portals according to the defined live validation matrix and record the result for each tested path.

**How to do it:**
1. Use the live apply validation matrix as the scope boundary.
2. Run BrowserOS-backed dry-run apply validations on each in-scope portal.
3. Persist evidence and outcomes.
4. Update docs if actual backend behavior differs from assumptions.

**Depends on:** none
