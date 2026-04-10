# Completed Plan Docs Artifacts Have Not Been Pruned

**Explanation:** Planning artifacts in `plan_docs/` should not remain after a feature is fully implemented. Once the implementation is complete and the needed knowledge is absorbed into code and documentation, the completed planning artifact should be deleted. The repository still contains long-lived planning material that needs this review.

**Reference:**
- `plan_docs/automation/`
- `plan_docs/ariadne/`
- `plan_docs/contracts/`
- `plan_docs/motors/`
- `AGENTS.md`

**What to fix:** Identify planning artifacts whose tracked feature or design work is already fully implemented, make sure their essential knowledge is absorbed into canonical docs or code-adjacent documentation, and delete the completed planning artifacts.

**How to do it:**
1. Review the remaining `plan_docs/` trees for artifacts whose implementation status is effectively complete.
2. Confirm the important design and operational knowledge has been captured in code, tests, READMEs, or canonical docs.
3. Fill any documentation gaps needed before deletion.
4. Delete the completed planning artifact once its knowledge is fully absorbed.

**Depends on:** none
