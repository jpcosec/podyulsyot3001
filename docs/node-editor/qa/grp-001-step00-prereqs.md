# GRP-001 Step 00 QA Prerequisites

## Scope

- Step: `SPEC_GRP_001_step00_prereqs.md`
- Goal: validate Step 00 prerequisites (data-provider pathing, worker assumptions, QA sequencing) without depending on Step 01+ implementation artifacts.

## Out of scope

- Do not validate unresolved imports inside future-step code snippets (for example, Step 10).

## Data provider baseline

- Concrete provider module is available at `apps/review-workbench/src/features/graph-editor/lib/data-provider.ts`.
- Provider exports `graphDataProvider` with `getSchema`, `getGraph`, and `saveGraph`.
- Module is importable with workspace alias style (`@/features/graph-editor/lib/data-provider`).

## Worker support baseline

- Worker entry exists at `apps/review-workbench/src/features/graph-editor/L2-canvas/workers/elk.worker.ts`.
- Factory uses the required constructor pattern:
  - `new Worker(new URL('../workers/elk.worker.ts', import.meta.url), { type: 'module' })`
- This matches Vite module-worker support assumptions for upcoming ELK integration.

## QA strategy for GRP sequence

- Local verification is required per step (typecheck/build/test for touched modules).
- E2E is deferred and consolidated at final validation step:
  - `plan/steps/step-05-final-validation.md`
- UI baseline dependency remains explicit:
  - Run `SPEC_UI_001_01_install_components.md` before UI-dependent GRP steps.
