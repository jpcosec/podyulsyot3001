# Restore: Danger Detection Capability

**Explanation:** During the Epic 0 purge, the original keyword-based CAPTCHA detection was removed. While the Mode system supports `inspect_danger`, the implementation is currently a stub. We need to restore the logic that scans the page for security blocks.

**Reference:** 
- `src/automation/ariadne/modes/portals.py`
- `src/automation/ariadne/modes/configs/danger_detection.json`

**What to fix:** Functional logic in `JsonConfigMode.inspect_danger` that matches snapshot text against the rules in `danger_detection.json`.

**How to do it:**
1.  Load the `danger_detection.json` config in the `ModeRegistry` or within the mode.
2.  Implement a string-matching loop that checks for security keywords.
3.  Ensure the `ObserveNode` reacts correctly to danger findings by routing to HITL.

**Depends on:** none
