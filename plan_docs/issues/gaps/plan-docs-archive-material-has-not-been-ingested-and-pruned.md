# Plan Docs Archive Material Has Not Been Ingested And Pruned

**Explanation:** `plan_docs/archive/` is meant to be transitional, but it still contains historical planning material. The repository rule is to absorb any still-relevant content into canonical docs or code-adjacent documentation, then delete the archive file instead of leaving long-lived duplicates behind.

**Reference:**
- `plan_docs/archive/automation/2026-04-03-unified-automation-refactor-plan.md`
- `plan_docs/archive/automation/asset_placement.md`
- `plan_docs/archive/automation/directory_glossary.md`
- `plan_docs/archive/automation/round_1_gemini.md`
- `plan_docs/archive/automation/round_1_gpt.md`
- `plan_docs/archive/automation/superpowers_audit.md`
- `AGENTS.md`

**What to fix:** Audit the archive files, ingest any still-useful content into canonical documentation or code-adjacent docs, and delete archive files whose knowledge has been absorbed or deemed obsolete.

**How to do it:**
1. Review each archive file and extract any remaining information that is not already covered by current code, READMEs, or docs.
2. Merge the still-relevant content into canonical docs near the owning module or into top-level docs when cross-cutting.
3. Verify the absorbed material is represented clearly enough that the archive file is no longer needed.
4. Delete the archive file after absorption or explicit obsolescence review.

**Depends on:** none
