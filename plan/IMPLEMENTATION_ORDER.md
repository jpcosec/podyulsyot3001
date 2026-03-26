# Implementation Order — Node Editor 3-Layer Architecture

> **Updated:** 2026-03-26
> **Status:** Ready to implement (normalized)

---

## PHASE 0: PREREQUISITES (DO NOT SKIP)

Before implementation, validate these prerequisites:

1. **Data provider is defined**
   - Either `@/mock/client` exists and is documented
   - Or L1 uses a real `fetch` provider with known endpoints
2. **UI foundation is installed**
   - Run `UI-001-01` before any GRP step that mounts shadcn components
3. **Worker support is verified**
   - Build tool must support `new Worker(new URL('./elk.worker.ts', import.meta.url))`
4. **QA strategy is explicit**
   - Local verification required per step
   - E2E runs only at final validation

---

## PHASE 1: IMPLEMENTATION

| Order | Step | File | Key points |
|-------|------|------|------------|
| 00 | GRP-001-00 | `SPEC_GRP_001_step00_prereqs.md` | Data provider + worker + QA bootstrap |
| 01 | UI-001-01 | `SPEC_UI_001_01_install_components.md` | shadcn install is blocking |
| 02 | GRP-001-01 | `SPEC_GRP_001_step1_stores.md` | Semantic history, `isVisualOnly` |
| 03 | GRP-001-02 | `SPEC_GRP_001_step02_schema_libs.md` | Contract aligned with stores/registry |
| 04 | GRP-001-03 | `SPEC_GRP_001_step03_registry.md` | Placeholders only, avoid circular deps |
| 05 | GRP-001-04 | `SPEC_GRP_001_step04_l3_components.md` | Replace placeholders with real L3 |
| 06 | GRP-001-05 | `SPEC_GRP_001_step05_graph_canvas.md` | Controlled drag updates + semantic commit |
| 07 | GRP-001-06 | `SPEC_GRP_001_step06_edges.md` | FloatingEdge, ButtonEdge |
| 08 | GRP-001-07 | `SPEC_GRP_001_step07_sidebar.md` | Sidebar sections |
| 09 | GRP-001-08 | `SPEC_GRP_001_step08_panels.md` | Node/Edge inspectors |
| 10 | GRP-001-09 | `SPEC_GRP_001_step09_hooks.md` | ELK worker + edge inheritance |
| 11 | GRP-001-10 | `SPEC_GRP_001_step10_l1_page.md` | L1 orchestrator, no phantom imports |
| 12 | GRP-001-11 | `SPEC_GRP_001_step11_theming.md` | xy-theme.css tokens |

## PHASE 1B: UI REFINEMENT (AFTER GRP BASE)

| Order | Task | File | Depends on |
|-------|------|------|------------|
| 13 | UI-001-02 Sidebar Accordion | `SPEC_UI_001_02_sidebar_accordion.md` | GRP-001-07 |
| 14 | UI-001-03 Node Sheet | `SPEC_UI_001_03_node_sheet.md` | GRP-001-08 |
| 15 | UI-001-04 Edge Sheet | `SPEC_UI_001_04_edge_sheet.md` | GRP-001-08 |
| 16 | UI-001-05 Property Inputs | `SPEC_UI_001_05_property_inputs.md` | GRP-001-04, GRP-001-08 |
| 17 | UI-001-06 Delete Dialog | `SPEC_UI_001_06_delete_dialog.md` | GRP-001-05 |
| 18 | UI-001-07 Filter UI | `SPEC_UI_001_07_filter_ui.md` | GRP-001-07 |
| 19 | UI-001-08 Creation Popover | `SPEC_UI_001_08_creation_popover.md` | GRP-001-07 |
| 20 | UI-001-09 Context Menu | `SPEC_UI_001_09_context_menu.md` | GRP-001-05 |
| 21 | UI-001-10 Command Dialog | `SPEC_UI_001_10_command_dialog.md` | GRP-001-07 |
| 22 | UI-001-11 Sonner | `SPEC_UI_001_11_sonner.md` | GRP-001-10 |

---

## PHASE 2: DOCUMENTATION + CLEANUP

| Order | Task | File | Description |
|-------|------|------|-------------|
| 23 | DOC-01 | `step-01-commit-and-tag.md` | Tag completed GRP/UI steps |
| 24 | DOC-02 | `step-02-create-docs.md` | Publish final docs with valid links |
| 25 | DOC-03 | `step-03-cleanup-plan.md` | Safe cleanup (desreference -> archive -> delete) |
| 26 | DOC-04 | `step-04-create-future.md` | Maintain deferred feature specs |
| 27 | DOC-05 | `step-05-final-validation.md` | Final E2E + regression matrix |

---

## Legacy policy

- Keep `KnowledgeGraph.tsx` as migration reference during implementation.
- Optional rename to `KnowledgeGraph.legacy.tsx`.
- Delete only after Step 10 is stable and Step 27 passes.

---

## Critical checkpoints

| Moment | Verify |
|--------|--------|
| After Step 00 | Data provider resolves, worker compiles, QA policy defined |
| After Step 05 | Registry renderers resolve with no circular imports |
| After Step 06 | Drag is smooth while moving, undo history remains semantic |
| After Step 11 | Schema -> graph -> save roundtrip works |
| After Step 27 | E2E integration and regressions pass |

---

## Documentation

| Need | Go to |
|------|-------|
| Avoid errors | `docs/node-editor/architecture_pitfalls.md` |
| Quick reference | `docs/node-editor/README.md` |
| Step by step | `plan/steps/README.md` |
| Specs | `plan/steps/SPEC_GRP_001_*.md` |
