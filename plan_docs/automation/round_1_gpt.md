# Round 1 GPT Review

## Logic check

- The phase order in `plan_docs/automation/2026-04-03-unified-automation-refactor-plan.md` is logically strong: documentation first, then contracts, then entrypoint shape, then persistence and engine moves. That sequencing lowers the risk of doing a file move before the ownership model is clear.
- `plan_docs/automation/asset_placement.md` is a good control document. Requiring each asset to be classified before it moves is the right guardrail against migration drift and accidental folder-by-folder reshuffling.
- The Ariadne common-language issues document is also useful because it exposes abstraction problems before code hardens around one backend.

## Main risks

- The target architecture may be wider than the current worktree goal. The plan includes `vision`, `os_native_tools`, BrowserOS agent flows, Ariadne promotion, and compiler-style translators. That is coherent as a long-term system shape, but risky if this branch is only meant to solve the browser automation pipeline issue.
- Ariadne still has several unresolved semantics before Phase 2. In `plan_docs/automation/2026-04-04-ariadne-common-language-issues.md`, target resolution, recording normalization, fallback semantics, and error taxonomy are still open. If implementation starts before those are narrowed, the first backend implemented may accidentally define the common language.
- There is a likely over-abstraction risk in portal definitions. If portals are authored now with fields for future motors that do not exist yet, the current authoring burden may grow faster than the practical value.
- The playbook ownership move is conceptually clean but operationally risky. Moving packaged playbooks from `src/apply/playbooks/` into Ariadne assets changes both runtime loading and conceptual ownership at the same time.

## Recommendation

- Treat BrowserOS CLI plus current apply/scrape integration as the mandatory slice.
- Keep Phase 2 minimal at first: target descriptor, fallback semantics, and common error taxonomy.
- Defer `vision`, `os_native_tools`, and agent-normalization work unless they directly unblock the current browser automation issue.
- Avoid building the full framework before proving the narrow path works end to end.
