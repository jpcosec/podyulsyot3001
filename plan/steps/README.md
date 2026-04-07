# plan/steps — Implementation Steps

Each file is one discrete, agent-executable task. Execute in order.

---

## Implementation (COMPLETE ✓)

| Order | Step | Task | Status |
|-------|------|------|--------|
| 00 | GRP-001-00 | Prerequisites (data provider, worker support, QA bootstrap) | ✓ |
| 01 | UI-001-01 | Install shadcn components | ✓ |
| 02 | GRP-001-01 | Zustand stores (graph-store, ui-store) | ✓ |
| 03 | GRP-001-02 | Schema translation (schemaToGraph, graphToDomain) | ✓ |
| 04 | GRP-001-03 | Node Registry with validation (placeholders only) | ✓ |
| 05 | GRP-001-04 | L3 Content (EntityCard, PropertiesPreview, PropertyEditor) | ✓ |
| 06 | GRP-001-05 | GraphCanvas (ReactFlow wrapper + render tiers) | ✓ |
| 07 | GRP-001-06 | Custom edges (FloatingEdge, ButtonEdge) | ✓ |
| 08 | GRP-001-07 | Sidebar (Actions, Filters, Creation, View) | ✓ |
| 09 | GRP-001-08 | Inspector Panels (NodeInspector, EdgeInspector) | ✓ |
| 10 | GRP-001-09 | Hooks (useGraphLayout, useEdgeInheritance, useKeyboard) | ✓ |
| 11 | GRP-001-10 | L1 Page (orchestrator) | ✓ |
| 12 | GRP-001-11 | xy-theme.css (theming) | ✓ |
| 13 | UI-001-02 | Sidebar Accordion | ✓ |
| 14 | UI-001-03 | Node Sheet | ✓ |
| 15 | UI-001-04 | Edge Sheet | ✓ |
| 16 | UI-001-05 | Property Inputs | ✓ |
| 17 | UI-001-06 | Delete Dialog | ✓ |
| 18 | UI-001-07 | Filter UI | ✓ |
| 19 | UI-001-08 | Creation Popover | ✓ |
| 20 | UI-001-09 | Context Menu | ✓ |
| 21 | UI-001-10 | Command Dialog | ✓ |
| 22 | UI-001-11 | Sonner | ✓ |

---

## Documentation (COMPLETE ✓)

| Order | Step | Task | File | Status |
|-------|------|------|------|--------|
| 23 | DOC-01 | Commit and tag | `step-01-commit-and-tag.md` | ✓ |
| 24 | DOC-02 | Create docs | `step-02-create-docs.md` | ✓ |
| 25 | DOC-03 | Cleanup plan | `step-03-cleanup-plan.md` | ✓ |
| 26 | DOC-04 | Create future/ | `step-04-create-future.md` | ✓ |
| 27 | DOC-05 | Final validation | `step-05-final-validation.md` | ✓ |

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
