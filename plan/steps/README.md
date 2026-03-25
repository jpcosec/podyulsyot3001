# plan/steps — Implementation Steps

Each file is one discrete, agent-executable task. Execute in order.

---

## Phase 0 — Prerequisites (one-time)

| Step | Task | Status |
|------|------|--------|
| UI-001-01 | Install shadcn components | ☐ |

---

## Phase 1 — Data Foundation (first!)

> **Why schema first?** Real data to test UI against, validation early, type safety from start

| Step | Task | Status |
|------|------|--------|
| GRP-001-01 | Zustand stores (graph-store, ui-store) | ☐ |
| GRP-001-02 | Schema translation (schemaToGraph, graphToDomain) — work with real data | ☐ |

---

## Phase 2 — Type System

| Step | Task | Status |
|------|------|--------|
| GRP-001-03 | Node Registry with validation | ☐ |

---

## Phase 3 — UI Components (consume data from Phase 1)

| Step | Task | Status |
|------|------|--------|
| GRP-001-04 | L3 Content (EntityCard, PropertiesPreview, PropertyEditor, PlaceholderNode) | ☐ |
| GRP-001-05 | GraphCanvas (ReactFlow wrapper + render tiers) | ☐ |
| GRP-001-06 | Custom edges (FloatingEdge, ButtonEdge) | ☐ |

---

## Phase 4 — Integration

| Step | Task | Status |
|------|------|--------|
| GRP-001-07 | L1 Page (orchestrator — fetches data, translates, renders canvas) | ☐ |

---

## Phase 5 — Editor Controls

| Step | Task | Status |
|------|------|--------|
| GRP-001-08 | Sidebar (Actions, Filters, Creation, View sections) | ☐ |
| GRP-001-09 | Inspector Panels (NodeInspector, EdgeInspector with Sheet) | ☐ |
| GRP-001-10 | Hooks (useGraphLayout, useEdgeInheritance, useKeyboard) | ☐ |

---

## Phase 6 — CSS / Theming

| Step | Task | Status |
|------|------|--------|
| GRP-001-11 | xy-theme.css (node color tokens, edge styles, dark mode, touch support) | ☐ |

---

## UI Enhancements (PARALLEL with GRP)

> **Note:** UI-001 steps can run in parallel with GRP-001 after UI-001-01 completes. They migrate existing UI to shadcn components.

| Step | Task | Status | Runs After |
|------|------|--------|------------|
| UI-001-02 | Sidebar Accordion | ☐ | UI-001-01 |
| UI-001-03 | Node Sheet | ☐ | UI-001-01 |
| UI-001-04 | Edge Sheet | ☐ | UI-001-01 |
| UI-001-05 | Property Inputs | ☐ | UI-001-01 |
| UI-001-06 | Delete Dialog | ☐ | UI-001-01 |
| UI-001-07 | Filter UI | ☐ | UI-001-01 |
| UI-001-08 | Creation Popover | ☐ | UI-001-01 |
| UI-001-09 | Context Menu | ☐ | UI-001-01 |
| UI-001-10 | Command Dialog | ☐ | UI-001-01 |
| UI-001-11 | Sonner | ☐ | UI-001-01 |

---

## Cleanup Steps (after all above complete)

| Step | Task | Status |
|------|------|--------|
| step-01 | Commit and tag completed steps | ☐ |
| step-02 | Create updated documentation | ☐ |
| step-03 | Clean up plan directory | ☐ |
| step-04 | Create FUTURE.md roadmap | ☐ |

---

## Spec Overview

- **GRP-001:** Graph Editor refactor - `SPEC_GRP_001.md`
- **UI-001:** Shadcn UI migration - `SPEC_UI_001.md`

---

## Reference

- Architecture: `plan/ARCHITECTURE.md`
- Blueprint: `plan/_meta/blueprint_node_editor.md`
- ReactFlow patterns: `plan/_meta/reactflow_patterns_catalog.md`
- Known problems: `plan/_meta/architecture_critique.md`
- E2E Testing: `plan/_meta/testsprite_product.md`