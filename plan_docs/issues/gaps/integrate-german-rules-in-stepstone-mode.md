# Integrate: German Rules in StepStone Mode

**Explanation:** The `StepStoneMode` currently only loads `stepstone.json` but ignores the common German language rules in `de_DE.json`. This means it lacks the "vollzeit/teilzeit" normalization and location cleanup rules extracted from Ariadne 1.0.

**Reference:** 
- `src/automation/ariadne/modes/portals.py`
- `src/automation/ariadne/modes/configs/de_DE.json`

**What to fix:** `StepStoneMode` must load both portal-specific and language-specific configs to handle German job postings.

**How to do it:**
1.  Update `JsonConfigMode` to allow multiple config file paths.
2.  Configure `StepStoneMode` to include `de_DE.json` in its rule registry.
3.  Implement the logic to apply these multi-config rules during `normalize_job`.

**Depends on:** none
