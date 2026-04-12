# unified-automation Issues Index

This file is the entrypoint for subagents deployed to solve issues in this repository.

All issue-fixing work must stay aligned with the rest of plan_docs/ and wiki/, with special care for wiki/standards/ so implementation, tests, and documentation remain consistent with the project's rules.

## Working rule for every issue

Once an issue is solved, the next step is always:

 1. Check whether any existing test is no longer valid and delete it if needed.
 2. Add new tests where necessary.
 3. Run the relevant tests.
 4. Update changelog.md.
 5. Delete the solved issue from both this index and the corresponding file in plan_docs/issues/.
 6. Make a commit that clearly states what was fixed, making sure all required files are staged.

## Priority roadmap

### Phase 1 — Content Restoration & Polish

 1. plan_docs/issues/gaps/implement-llm-fallback-in-default-mode.md

 2. plan_docs/issues/gaps/integrate-german-rules-in-stepstone-mode.md

 3. plan_docs/issues/gaps/fix-stepstone-apply-button-selector.md

    • [1, 2, 3 are parallelizable]

### Phase 2 — Live Validation

 4. plan_docs/issues/gaps/validate-live-apply-on-portals.md • depends on plan_docs/issues/gaps/fix-stepstone-apply-button-selector.md, plan_docs/issues/gaps/integrate-german-rules-in-stepstone-mode.md

## Dependency summary

• plan_docs/issues/gaps/validate-live-apply-on-portals.md  ->  plan_docs/issues/gaps/fix-stepstone-apply-button-selector.md
• plan_docs/issues/gaps/validate-live-apply-on-portals.md  ->  plan_docs/issues/gaps/integrate-german-rules-in-stepstone-mode.md

## Parallelization map

Phase 1  [1][2][3]          ← [Content & Polish] Phase 2     [4]          ← [Validation]
