# Implement: LinkedIn Portal Mode Logic

**Explanation:** The `LinkedInMode` is currently a placeholder. We need to implement the specific normalization and heuristic rules for LinkedIn, extracting them from the legacy code (if applicable) or defining new rules based on LinkedIn's UI behavior.

**Reference:** 
- `src/automation/ariadne/modes/portals.py`
- `plan_docs/ariadne/portals_and_modes.md`

**What to fix:** A fully functional `LinkedInMode` that cleans job payloads and identifies LinkedIn-specific UI states.

**How to do it:**
1.  Implement `normalize_job` using rules from `src/automation/ariadne/modes/configs/linkedin.json`.
2.  Implement `apply_local_heuristics` to handle LinkedIn's unique "Next" button patterns.
3.  Implement `inspect_danger` for LinkedIn-specific bot detection pages.

**Depends on:** none
