# Canonical Job Normalization Is Not Owned By Ariadne

**Explanation:** The real-data scrape issues show that canonicalization of job data is a semantic concern, but it currently lives mostly inside the Crawl4AI motor path instead of being explicitly modeled as part of Ariadne's neutral layer. Ariadne is supposed to be the semantic center of the automation system, yet raw portal cleanup and pre-validation canonicalization are implemented ad hoc inside `src/automation/motors/crawl4ai/scrape_engine.py`.

That creates an architectural mismatch:
1. motors and portal-specific extractors return noisy, unstable, source-shaped data
2. canonical cleanup rules are semantic and cross-portal in nature
3. but those rules are not owned by Ariadne, so they are harder to reuse, test, reason about, and extend across backends

In practice, this means the system has a pre-Ariadne semantic layer hidden inside a motor implementation. That weakens backend neutrality and makes it harder to define a clean contract for what counts as a canonical job posting before apply/routing logic consumes it.

**Reference:**
- `src/automation/ariadne/models.py`
- `src/automation/ariadne/`
- `src/automation/motors/crawl4ai/scrape_engine.py`
- `plan_docs/issues/gaps/extraction-and-canonical-normalization-are-not-explicitly-separated.md`

**What to fix:** Move ownership of canonical job normalization into an Ariadne-adjacent semantic layer. Motors should extract raw data; Ariadne should own the normalization rules and the `raw -> cleaned -> extracted` contract boundary before `JobPosting` validation.

**How to do it:**
1. Define where canonical job normalization belongs in Ariadne (`src/automation/ariadne/` or an adjacent neutral layer).
2. Move cross-portal cleanup rules out of motor-specific code into that semantic layer.
3. Make Ariadne own the semantic contract for three outputs: `raw`, `cleaned`, and `extracted`.
4. Keep motor-specific extraction and selector logic in motors, but make the canonicalization contract backend-neutral.
5. Add tests at the semantic layer using real artifact samples from XING, StepStone, and TU Berlin.
6. Ensure both Crawl4AI extraction and BrowserOS rescue feed the same Ariadne-owned normalization pipeline.

**Depends on:** none
