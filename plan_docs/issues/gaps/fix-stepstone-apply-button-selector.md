# Fix: StepStone Apply Button Selector

**Explanation:** In live job runs, the `open_modal` step for StepStone fails because the current selector `[data-at='apply-button']` is not found. This is a known portal drift issue that blocks automated applications on this portal.

**Reference:** 
- `QA_BACKLOG.md`
- `src/automation/portals/stepstone/maps/easy_apply.json`

**What to fix:** Update the StepStone map with a working selector for the apply button.

**How to do it:**
1.  Run a live observation on a StepStone job.
2.  Identify the current working CSS selector or text for the apply button.
3.  Update the `job_details` state in `src/automation/portals/stepstone/maps/easy_apply.json`.

**Depends on:** none
