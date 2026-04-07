# Agent Reviewer Entrypoint

Use this file as the entrypoint prompt for a reviewing/planning agent working on the node editor roadmap.

## Mission

Review the roadmap as a dependency graph, not as isolated features.

## Read first

1. `plan/steps/README.md`
2. `plan/IMPLEMENTATION_ORDER.md`
3. `plan/ARCHITECTURE.md`
4. `docs/node-editor/README.md`
5. `docs/node-editor/architecture_pitfalls.md`

Then read the specific step files relevant to the feature under review.

## Source code anchors

- `apps/review-workbench/src/pages/global/KnowledgeGraph.tsx`
- `apps/review-workbench/src/sandbox/pages/NodeEditorSandboxPage.tsx`
- `apps/review-workbench/src/sandbox/pages/CvGraphEditorPage.tsx`
- `apps/review-workbench/src/api/client.ts`

## Review questions

For any proposed implementation, answer these in order:

1. Which plan step does this belong to?
2. What are its hard dependencies?
3. Is each dependency implemented, partial, or missing?
4. What state contracts or payload shapes would change?
5. What breaks if we implement this now?
6. What can be deferred safely?
7. What is the smallest reviewable vertical slice?

## Output format

- `Target step`
- `Depends on`
- `Blocked by`
- `Break risk`
- `Recommended smallest slice`
- `Local verification checklist`
- `Libraries to evaluate`

## Rule

Do not recommend adding a rich widget directly into the graph editor unless the answer explicitly confirms:

- node type registry is sufficient
- persistence shape is known
- annotation/reference identity is known
- test impact is bounded
