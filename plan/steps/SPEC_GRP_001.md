# Spec GRP-001 — Graph Editor (Node Editor Refactor)

**Feature:** Refactor KnowledgeGraph.tsx to 3-layer architecture
**Context:** 2,949-line God Component → modular, testable, maintainable
**Phase:** Main implementation

---

## Objective

Refactor the node editor from a single monolithic component to:
- **L1 (App):** Data fetching, schema translation, orchestration
- **L2 (Canvas):** ReactFlow wrapper, sidebar, panels, hooks
- **L3 (Content):** Reusable components (EntityCard, PropertyEditor)

With Zustand stores, Node Registry, and shadcn UI components.

---

## Architecture

```
L1: GraphEditorPage
  ├── schemaToGraph() → AST nodes/edges
  └── <GraphCanvas /> + <CanvasSidebar /> + <Inspector />

L2: GraphCanvas
  ├── ReactFlow with custom nodeTypes/edgeTypes
  ├── NodeShell (render tiers: dot/label/detail)
  ├── GroupShell (collapse/expand)
  ├── FloatingEdge, ButtonEdge
  ├── CanvasSidebar (Accordion sections)
  ├── NodeInspector, EdgeInspector (Sheet)
  └── Hooks (layout, keyboard, edge inheritance)

L3: Content (reusable)
  ├── EntityCard
  ├── PropertiesPreview
  ├── PropertyEditor
  └── PlaceholderNode
```

---

## Key Components

| Layer | Component | Description |
|-------|-----------|-------------|
| L1 | GraphEditorPage | Orchestrator - fetch, translate, render |
| L2 | GraphCanvas | ReactFlow wrapper |
| L2 | NodeShell | Base node with zoom-based render tiers |
| L2 | GroupShell | Collapsible group node |
| L2 | FloatingEdge | Bezier edge with intersection |
| L2 | ButtonEdge | Edge with delete button |
| L2 | CanvasSidebar | Accordion sections |
| L2 | NodeInspector | Sheet panel for node editing |
| L2 | EdgeInspector | Sheet panel for edge editing |
| L3 | EntityCard | Title + category + badges |
| L3 | PropertiesPreview | Collapsible key/value table |
| L3 | PropertyEditor | Multi-type input fields |
| L3 | PlaceholderNode | Skeleton for zoom-out |

---

## State Management

**graph-store (Zustand):**
- nodes, edges, undoStack, redoStack
- addElements, removeElements, updateNode, updateEdge
- undo, redo, loadGraph, isDirty, markSaved

**ui-store (Zustand):**
- editorState, focusedNodeId, focusedEdgeId
- sidebarOpen, filters, copiedNodeId
- setEditorState, setFocusedNode, setFilter

---

## Schema Pipeline

```
rawData → schemaToGraph() → AST (nodes + edges) → ReactFlow
AST ← graphToDomain() ← save
```

Validation errors produce ErrorNode, not crashes.

---

## Dependencies

- Step GRP-001-01 (stores) first
- Step GRP-001-02 (schema) second - real data for rest
- Steps 04-10 depend on 01-03

---

## Reference

- Blueprint: `plan/_meta/blueprint_node_editor.md`
- Architecture: `plan/ARCHITECTURE.md`
- ReactFlow patterns: `plan/_meta/reactflow_patterns_catalog.md`