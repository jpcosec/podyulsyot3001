# Implement: StepStone Portal Mode Logic

**Explanation:** The `StepStoneMode` is currently a placeholder. We need to implement the specific normalization and heuristic rules for StepStone, especially focusing on the German keyword extraction and location cleanup rules identified in the audit.

**Reference:** 
- `src/automation/ariadne/modes/portals.py`
- `plan_docs/ariadne/portals_and_modes.md`

**What to fix:** A fully functional `StepStoneMode` that handles German job data and StepStone-specific UI recovery.

**How to do it:**
1.  Implement `normalize_job` using rules from `src/automation/ariadne/modes/configs/de_DE.json`.
2.  Implement `apply_local_heuristics` to handle StepStone's "Ich bin interessiert" vs "Apply" variations.
3.  Implement `inspect_danger` for StepStone security interstitials.

**Depends on:** none
