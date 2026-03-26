# Changelog

## 2026-03-26

- Normalized implementation planning docs for node editor refactor.
- Fixed ordering/dependency conflicts across `plan/steps/README.md` and `plan/IMPLEMENTATION_ORDER.md`.
- Added preflight and final validation steps (`SPEC_GRP_001_step00_prereqs.md`, `step-05-final-validation.md`).
- Updated key specs to avoid circular dependency traps, phantom imports, and drag/history inconsistencies.
- Replaced per-step E2E expectations with local verification guidance and consolidated E2E at the end.
- Repaired core documentation links and updated reviewer entrypoint to real repository paths.
- Added GRP-001 Step 00 prereq artifacts: graph data provider module, worker smoke baseline, and QA preflight documentation.
- Implemented UI-001-01 shadcn setup in `apps/review-workbench` with required UI primitives and utility wiring.
- Implemented GRP-001-01 store foundations with Zustand graph/ui stores, semantic undo-redo primitives, and store unit tests.
- Implemented GRP-001-02 schema translation libraries with raw-to-AST/domain mappers and coverage tests.
- Implemented GRP-001-03 node type registry with Zod-backed validation, placeholder default registrations, and registry tests.
- Implemented GRP-001-04 L3 content components and wired registry detail renderers to real `EntityCard` content.
- Implemented GRP-001-05 graph canvas layer with `GraphCanvas`, `NodeShell`, and `GroupShell`, including controlled drag semantics and render tiers.
- Implemented GRP-001-06 custom edge layer with `FloatingEdge`, `ButtonEdge`, and shared edge helpers wired into `GraphCanvas` edge types.
- Implemented GRP-001-07 sidebar layer with `CanvasSidebar` and Actions/Filters/Creation/View accordion sections wired to graph/UI stores.
- Implemented GRP-001-08 inspector panel layer with `NodeInspector` and `EdgeInspector` sheets wired to UI focus state and graph store updates.
- Fixed GRP-001-08 node property persistence so inspector add/edit/delete/rename updates replace property maps correctly.
- Implemented GRP-001-09 hooks layer with ELK worker layout, edge inheritance collapse/expand behavior, and global keyboard shortcuts wired into L2 canvas components.
- Implemented GRP-001-10 L1/L2 integration with `GraphEditorPage` orchestrating schema registration + graph loading and new `GraphEditor` container composing canvas, sidebar, inspector panels, and toaster.
