# BrowserOS XING Live Apply Is Not Validated

**Explanation:** The BrowserOS backend is part of the supported apply architecture, but its end-to-end behavior for the XING portal has not been validated on real authenticated apply pages.

**Reference:**
- `src/automation/motors/browseros/`
- `docs/automation/live_apply_validation_matrix.md`

**What to fix:** Validate the BrowserOS apply backend on the live XING portal according to the live validation matrix (dry-run).

**How to do it:**
1. Ensure a valid XING BrowserOS session exists.
2. Run a BrowserOS-backed dry-run apply validation on a real XING job posting.
3. Persist evidence and record the outcome (reaches dry-run stop or fails with documented routing/apply reason).
4. Update docs if actual backend behavior differs from assumptions.

**Depends on:** none
