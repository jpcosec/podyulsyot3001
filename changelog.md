# Changelog

## 2026-04-08

- **Fixed graph rendering issues:**
  - GAP-01: Unknown nodes fallback to "entity" type instead of showing error boxes
  - GAP-02: Group nodes show colored borders (document=purple, section=blue)
  - GAP-03: Edge labels show relation type on hover
  - GAP-04: Group border colors now use category mapping
  - GAP-05: Node border colors now use category mapping (entry=green, concept=blue)
  - Implemented UI-001-03 through UI-001-11 (Node Sheet, Edge Sheet, Property Inputs, Delete Dialog, Filter UI, Creation Popover, Context Menu, Command Dialog, Sonner)
  - Updated NodeShell and GroupShell to support both AST and direct JSON data formats
  - Added onNodesChange/onEdgesChange/onConnect to graph-store for ReactFlow integration
  - Added selectedNode/selectedEdge to ui-store
  - Fixed type definitions to support optional payload for direct JSON format
  - Fixed CSS @import order in styles.css
- Updated plan/README.md and plan/steps/README.md with completion status
- Created git tag v2.0.0-graph-editor-refactor

## 2026-04-03

- Raised the `apps/review-workbench` visual polish with a glassmorphism shell, atmospheric canvas framing, upgraded sidebar styling, and richer loading/error states.

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
- Implemented UI-001-02: Sidebar accordion migration (uses shadcn Accordion with type="multiple").
