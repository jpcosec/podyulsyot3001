# Superpowers Folder Audit

Date: 2026-04-03

Status: completed; the former `docs/superpowers/` tree has been removed after redistribution.

Purpose: identify what remained in the former superpowers docs folder, whether it was implemented, and what should be preserved, moved, or deleted under the repository documentation rules in `docs/standards/docs/documentation_and_planning_guide.md`.

## Summary

- Only one former superpowers file was clearly fully implemented.
- Most former superpowers files were partial or stale generate-documents design/spec material.
- Two important references were broken because they pointed to missing superpowers files.
- The folder was a good candidate for removal once the useful remnants were redistributed.

## File-by-file status

| File | Status | Recommended action |
|---|---|---|
| former `2026-03-31-generate-documents-v2-plan1-contracts-job-pipeline.md` | implemented | Move to `plan_docs/` only if still useful as historical migration context; otherwise archive/delete after ensuring `changelog.md` is enough. |
| former `2026-03-31-generate-documents-spec.md` | partial | Historical only in this worktree; preserve any still-useful automation-facing ideas in `plan_docs/automation/`. |
| former `2026-03-31-generate-documents-graph-spec.md` | partial | Historical only in this worktree; do not keep path references to removed graph modules. |
| former `2026-03-31-generate-documents-pydantic-contracts.md` | partial | Historical only in this worktree; extract only generic documentation lessons if needed. |
| former `2026-03-31-generate-documents-hitl-spec.md` | partial | Out of scope for this automation branch; avoid keeping review-ui references alive here. |
| former `2026-03-31-generate-documents-extension-guide.md` | stale | Delete or rewrite from scratch later when real extension seams exist. |
| former `2026-03-31-generate-documents-regional-cases.md` | stale | Out of scope for this worktree; keep no active reference. |
| former `2026-03-31-generate-documents-examples.md` | stale | Delete after extracting any examples that still match current output; otherwise it over-promises product behavior. |
| former `2026-03-31-generate-documents-delta-design.md` | stale | Treat as exploratory design and leave out of this worktree's active references. |
| former `2026-03-30-unmask-errors-move-translator.md` | partial | Out of scope after worktree reduction; do not preserve translator-specific path references here. |
| former `2026-03-29-pipeline-graph-unification.md` | stale | Keep deleted; it targets paths that no longer exist in this worktree. |

## Missing / broken references

These references pointed into the deleted superpowers folder and the target file did not exist:

- missing target: former apply module design spec (`2026-03-30-apply-module-design.md`)
  - referenced from:
    - `src/apply/README.md`
    - `src/apply/main.py`
    - `src/apply/models.py`
    - `src/apply/smart_adapter.py`
    - `src/apply/providers/xing/adapter.py`
    - `src/apply/providers/stepstone/adapter.py`
- missing target: former automation refactor plan path under superpowers
  - referenced from:
    - `plan_docs/automation/README.md`

## What appears not implemented yet

These themes appeared in the superpowers docs but are not fully implemented in code:

- richer generate-documents regional behavior
  - DIN 5008 and German-specific layout logic
  - Chile/Germany/academic branching
  - market-aware document strategy switching
- richer generate-documents extension surface
  - documented extension points are not really stabilized in code yet
- full generate-documents HITL patch flow
  - real `GraphPatch`-driven review/edit flow is not present for `generate_documents_v2`
- profile learning/updater loop
  - docs describe persistent learning from HITL feedback; code currently has only thin placeholders
- some translator/unmask-error plan leftovers
  - parts landed, but the original plan references old graph paths that no longer exist

## Recommended redistribution by repository rules

Based on `docs/standards/docs/documentation_and_planning_guide.md`:

### Keep near code

- current generate-documents-v2 architecture summary -> `src/core/ai/generate_documents_v2/README.md`
- current contracts overview -> same module README, pointing to contract files
- current browser-automation behavior -> keep it next to `src/apply/README.md` or inside `plan_docs/automation/`

### Keep out of scope

- every still-unimplemented generate-documents behavior that is not needed for browser automation

### Move to `plan_docs/`

- only active execution plans that are still meant to be worked on next
- if a plan is already done or stale, do not keep it in `plan_docs/`

### Delete

- stale exploratory superpowers specs that duplicate or overstate current behavior
- stale plans tied to removed paths once any remaining unresolved work is captured elsewhere

## Practical conclusion

Yes: there were still non-implemented things represented in the superpowers docs, mostly in the generate-documents specs.

If the goal is to kill the folder cleanly, the safest sequence is:

1. fix the broken references
2. extract only automation-relevant follow-up items into `plan_docs/automation/`
3. move current behavior summaries next to the relevant module README(s)
4. delete stale exploratory/spec-heavy files that no longer match the code
5. remove the superpowers docs folder
