# Live Portal Coverage Is Not Broad Enough

**Explanation:** The recent live validation proved the scrape pipeline on current XING, StepStone, and TU Berlin pages, but it does not yet establish that the system is robust across page variants within those portals or across the broader set of supported/expected portals. Current evidence is still narrow relative to the likely production surface.

This matters because one successful live sample per portal does not prove resilience against:
1. alternate job templates within the same portal
2. external ATS handoff variants
3. localized page variants and alternate heading structures
4. different listing-card shapes or ranking positions

**Reference:**
- `data/jobs/xing/`
- `data/jobs/stepstone/`
- `data/jobs/tuberlin/`
- `src/automation/motors/crawl4ai/scrape_engine.py`

**What to fix:** Expand live validation to cover multiple page variants per portal and document the current confidence envelope for each portal. This parent issue is atomized by portal so each validation set can be assigned independently.

**How to do it:**
1. Validate XING variants in `plan_docs/issues/gaps/xing-live-coverage-is-not-broad-enough.md`.
2. Validate StepStone variants in `plan_docs/issues/gaps/stepstone-live-coverage-is-not-broad-enough.md`.
3. Validate TU Berlin variants in `plan_docs/issues/gaps/tuberlin-live-coverage-is-not-broad-enough.md`.
4. Fold confirmed variants back into regression artifacts/tests.

**Depends on:** `plan_docs/issues/gaps/xing-live-coverage-is-not-broad-enough.md`, `plan_docs/issues/gaps/stepstone-live-coverage-is-not-broad-enough.md`, `plan_docs/issues/gaps/tuberlin-live-coverage-is-not-broad-enough.md`
