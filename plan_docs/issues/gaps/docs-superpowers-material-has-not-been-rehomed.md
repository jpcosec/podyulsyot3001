# Docs Superpowers Material Has Not Been Rehomed

**Explanation:** `docs/superpowers/` still contains planning and specification material that should not remain there as a permanent documentation home. The repository rule is that still-relevant material must be moved into `plan_docs/` so planning artifacts live in one consistent place.

**Reference:**
- `docs/superpowers/specs/2026-04-06-unified-automation-refactor-design.md`
- `docs/superpowers/plans/2026-04-06-unified-automation-migration.md`
- `docs/superpowers/plans/2026-04-06-ariadne-session-orchestrator.md`
- `AGENTS.md`

**What to fix:** Audit `docs/superpowers/`, move any still-relevant planning/spec content into the appropriate `plan_docs/` location, and remove the old `docs/superpowers/` copies once the knowledge has been rehomed.

**How to do it:**
1. Review each file under `docs/superpowers/` and classify each section as still-relevant, obsolete, or already absorbed.
2. Move still-relevant planning/spec content into the correct `plan_docs/` area.
3. Update any surviving references to point to the new `plan_docs/` location.
4. Delete the original `docs/superpowers/` files once their useful content is absorbed or declared obsolete.

**Depends on:** none
