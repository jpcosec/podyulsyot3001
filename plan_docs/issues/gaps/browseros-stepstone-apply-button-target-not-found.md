# BrowserOS StepStone Apply Button Target Not Found

**Explanation:** When running a BrowserOS dry-run apply on a live StepStone job, the `open_modal` step fails immediately because the mapped CSS target `css="[data-at='apply-button']"` is not found on the page. The live BrowserOS snapshot shows visible `Ich bin interessiert` buttons but they do not match the current selector, indicating the portal map does not match the live StepStone apply surface.

**Reference:**
- `src/automation/portals/stepstone/maps/easy_apply.json`
- `src/automation/portals/routing.py`
- `data/jobs/stepstone/13314431/nodes/apply/proposed/hitl/step-001/browseros_snapshot.txt`
- `data/jobs/stepstone/13314431/nodes/apply/meta/hitl_interrupt.json`
- `docs/automation/live_apply_validation_matrix.md`

**What to fix:** Update the StepStone apply portal map so the `open_modal` step uses a correct element target that matches the live StepStone apply surface, or add proper navigation pre-steps so the apply form is reached before the target is asserted.

**How to do it:**
1. Inspect the live BrowserOS snapshot at `data/jobs/stepstone/13314431/nodes/apply/proposed/hitl/step-001/browseros_snapshot.txt` to identify the actual apply button element (e.g. `Ich bin interessiert`) and its attributes.
2. Update the StepStone `easy_apply.json` portal map with the correct `css` or `text` selector for the apply button.
3. If the apply form requires a navigation pre-step, update the route to include that step.
4. Re-run the dry-run validation to confirm the `open_modal` step passes.
5. Update the live validation matrix evidence section once the flow works.

**Depends on:** none
