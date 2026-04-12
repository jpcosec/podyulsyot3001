# Validate: Live Apply on Portals

**Explanation:** Ariadne 2.0 has been implemented and unit-tested, but its ability to complete real job applications on live portals (LinkedIn, StepStone, XING) has not been validated end-to-end. We need to confirm that the fallback cascade and JIT execution work in the real world.

**Reference:** 
- `QA_BACKLOG.md`
- `src/automation/main.py`

**What to fix:** Completed live validation matrix for onsite apply flows across all supported motors.

**How to do it:**
1.  Run `python -m src.automation.main apply --dry-run` for at least 3 jobs per portal (LinkedIn, StepStone).
2.  Test with both `browseros` and `crawl4ai` motors.
3.  Document successes and atomize any failures into new gap issues.

**Depends on:** 
- `plan_docs/issues/gaps/fix-stepstone-apply-button-selector.md`
- `plan_docs/issues/gaps/integrate-german-rules-in-stepstone-mode.md`
