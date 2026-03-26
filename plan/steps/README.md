# plan/steps — Implementation Steps

Each file is one discrete, agent-executable task. Execute in order.

---

## Implementation (run first)

| Order | Step | Task | Status |
|-------|------|------|--------|
| 00 | GRP-001-00 | Prerequisites (data provider, worker support, QA bootstrap) | ☐ |
| 01 | UI-001-01 | Install shadcn components | ☐ |
| 02 | GRP-001-01 | Zustand stores (graph-store, ui-store) | ☐ |
| 03 | GRP-001-02 | Schema translation (schemaToGraph, graphToDomain) | ☐ |
| 04 | GRP-001-03 | Node Registry with validation (placeholders only) | ☐ |
| 05 | GRP-001-04 | L3 Content (EntityCard, PropertiesPreview, PropertyEditor) | ☐ |
| 06 | GRP-001-05 | GraphCanvas (ReactFlow wrapper + render tiers) | ☐ |
| 07 | GRP-001-06 | Custom edges (FloatingEdge, ButtonEdge) | ☐ |
| 08 | GRP-001-07 | Sidebar (Actions, Filters, Creation, View) | ☐ |
| 09 | GRP-001-08 | Inspector Panels (NodeInspector, EdgeInspector) | ☐ |
| 10 | GRP-001-09 | Hooks (useGraphLayout, useEdgeInheritance, useKeyboard) | ☐ |
| 11 | GRP-001-10 | L1 Page (orchestrator) | ☐ |
| 12 | GRP-001-11 | xy-theme.css (theming) | ☐ |
| 13 | UI-001-02 | Sidebar Accordion (depends on GRP-001-07) | ✓ |
| 14 | UI-001-03 | Node Sheet (depends on GRP-001-08) | ☐ |
| 15 | UI-001-04 | Edge Sheet (depends on GRP-001-08) | ☐ |
| 16 | UI-001-05 | Property Inputs (depends on GRP-001-04, GRP-001-08) | ☐ |
| 17 | UI-001-06 | Delete Dialog (depends on GRP-001-05) | ☐ |
| 18 | UI-001-07 | Filter UI (depends on GRP-001-07) | ☐ |
| 19 | UI-001-08 | Creation Popover (depends on GRP-001-07) | ☐ |
| 20 | UI-001-09 | Context Menu (depends on GRP-001-05) | ☐ |
| 21 | UI-001-10 | Command Dialog (depends on GRP-001-07) | ☐ |
| 22 | UI-001-11 | Sonner (depends on GRP-001-10) | ☐ |

---

## Documentation (run AFTER implementation)

| Order | Step | Task | File | Description |
|-------|------|------|------|-------------|
| 23 | DOC-01 | Commit and tag | `step-01-commit-and-tag.md` | Tag all completed steps |
| 24 | DOC-02 | Create docs | `step-02-create-docs.md` | Generate final docs |
| 25 | DOC-03 | Cleanup plan | `step-03-cleanup-plan.md` | Archive or remove temp files safely |
| 26 | DOC-04 | Create future/ | `step-04-create-future.md` | Deferred specs folder |
| 27 | DOC-05 | Final validation | `step-05-final-validation.md` | Consolidated E2E and regression checks |

---

## Quick Reference

| Need | Go To |
|------|-------|
| Avoid errors | `docs/node-editor/architecture_pitfalls.md` |
| Step-by-step | `plan/IMPLEMENTATION_ORDER.md` |
| Specs | `plan/steps/SPEC_GRP_001_*.md` |

---

## Legacy Retention Policy

Do not delete `apps/review-workbench/src/pages/global/KnowledgeGraph.tsx` at the beginning.

- Keep it as migration reference during GRP-001 and UI-001.
- Optional: rename to `KnowledgeGraph.legacy.tsx` to prevent accidental usage.
- Delete only after GRP-001-10 is stable and local validation passes.
