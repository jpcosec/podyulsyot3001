# BrowserOS StepStone Live Apply Is Not Validated

**Explanation:** The BrowserOS backend is part of the supported apply architecture, but its end-to-end behavior for the StepStone portal has not been validated on real authenticated apply pages.

**Reference:**
- `src/automation/motors/browseros/`
- `docs/automation/live_apply_validation_matrix.md`

**What to fix:** Validate the BrowserOS apply backend on the live StepStone portal according to the live validation matrix (dry-run).

**How to do it:**
1. Ensure a valid BrowserOS session exists if onsite apply is used.
2. Run a BrowserOS-backed dry-run apply validation on a real StepStone job posting.
3. Persist evidence and record the outcome (reaches dry-run stop or fails with documented email/external_url/unsupported routing outcome).
4. Update docs if actual backend behavior differs from assumptions.

**Depends on:** none
