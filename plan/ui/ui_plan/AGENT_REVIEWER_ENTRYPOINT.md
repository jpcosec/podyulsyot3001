# Agent Reviewer Entrypoint

Use this file as the entrypoint prompt for a reviewing/planning agent working on the UI roadmap.

## Mission

Review the UI roadmap as a dependency graph, not as isolated features.

## Read First

1. `plan/ui/ui_plan/README.md`
2. `plan/ui/ui_plan/00_status_matrix.md`
3. `plan/ui/ui_plan/01_graph_foundations.md`
4. `plan/ui/ui_plan/05_validation_and_test_impact_map.md`

Then read the specific node files relevant to the feature under review.

## Source Code Anchors

- `apps/review-workbench/src/sandbox/pages/NodeEditorSandboxPage.tsx`
- `apps/review-workbench/src/sandbox/pages/CvGraphEditorPage.tsx`
- `apps/review-workbench/src/sandbox/components/RichTextPane.tsx`
- `apps/review-workbench/src/api/client.ts`

## Review Questions

For any proposed implementation, answer these in order:

1. Which UI-plan node does this belong to?
2. What are its hard dependencies?
3. Is the dependency already implemented, partial, or missing?
4. What state contracts or payload shapes would change?
5. What breaks if we implement this now?
6. What can be deferred safely?
7. What is the smallest reviewable vertical slice?

## Output Format

- `Target node`
- `Depends on`
- `Blocked by`
- `Break risk`
- `Recommended smallest slice`
- `Verification checklist`
- `Libraries to evaluate`

## Rule

Do not recommend adding a rich widget directly into the graph editor unless the answer explicitly confirms:

- node type registry is sufficient
- persistence shape is known
- annotation/reference identity is known
- test impact is bounded
