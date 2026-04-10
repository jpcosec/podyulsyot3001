# Crawl4AI XING Live Apply Is Not Validated

**Explanation:** The Crawl4AI backend remains part of the apply system, but its end-to-end behavior for the XING portal has not been validated on real authenticated apply flows.

**Reference:**
- `src/automation/motors/crawl4ai/apply_engine.py`
- `docs/automation/live_apply_validation_matrix.md`

**What to fix:** Validate the Crawl4AI apply backend on the live XING portal according to the live validation matrix (dry-run).

**How to do it:**
1. Ensure portal-specific auth/profile exists if required.
2. Run a Crawl4AI-backed dry-run apply validation on a real XING job posting.
3. Persist evidence and record the outcome (reaches dry-run stop or fails with documented routing/apply reason).
4. Update docs or routing assumptions if live behavior differs from expectations.

**Depends on:** none
