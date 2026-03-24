# Spec D2 — Group Node Collapse / Expand

**Feature:** `src/pages/global/KnowledgeGraph.tsx` — `GroupNode` component + collapse logic
**Depends on:** D1 (SchemaExplorer, readOnly mode, CATEGORY_COLORS)
**Libraries:** `@xyflow/react` (NodeToolbar, NodeResizer, useReactFlow, useNodeId, useOnSelectionChange, node.hidden)

---

## Context

When planning collapse/expand in the future docs (`plan/future/02_structured_documents_and_subflows.md`), the design assumed we would need custom state management, proxy edge computation, and callback threading from the editor shell down to node components.

A review of the ReactFlow API (first batch: NodeToolbar, custom-node, sub-flows, intersections, drag-handle; second batch: computing-flows, drag-and-drop, selection-grouping, parent-child-relation, expand-collapse, floating-edges) reveals that several built-in primitives replace most of that work:

### First batch findings

| ReactFlow feature | What it gives us | Future-doc assumption it replaces |
|---|---|---|
| `NodeToolbar` | Floating, zoom-invariant button panel attached to a node — always legible | Header-inside-node-body with collapse toggle |
| `node.hidden` / `edge.hidden` | Native React Flow property — hidden nodes/edges stay in state but are not rendered | Manual filtering in `displayNodes` / proxy edge construction |
| `useReactFlow()` inside node components | Direct access to `setNodes` / `setEdges` from inside any node | Threading `onToggleCollapse` callback through `node.data` from `NodeEditorInner` |

### Second batch findings

| ReactFlow feature | What it gives us | Where it applies |
|---|---|---|
| **`useExpandCollapse` hook** (expand-collapse example) | Official ReactFlow pattern: full graph in memory, conditionally renders visible subset; Dagre layout recalculation on toggle | Replaces our hand-rolled `hidden` toggle — the example's hook is the reference implementation for our `useExpandCollapse` |
| **`NodeResizer`** (selection-grouping example) | Automatically adjusts group node dimensions based on children | Replaces manual `style.height` changes on collapse/expand; works with `parentId`/`extent: 'parent'` |
| **`useOnSelectionChange()`** (selection-grouping example) | Fires when node selection changes — detects multi-node selection for group creation | Enables "group selected nodes" action in the editor without a separate state machine |
| **`useNodeId()`** (parent-child example) | Returns current node's ID inside a custom node component — no prop threading | Replaces `node.data.nodeId` pattern we currently use in `SimpleNodeCard` and `GroupNode` |
| **`screenToFlowPosition()`** (drag-and-drop example) | Converts screen coords to canvas coords on drop | Already used for drop targets; confirms our pattern is correct |
| **Position recalculation on reparenting** (parent-child example) | When a node is absorbed into a group, must convert absolute → parent-relative coords: `child.position = { x: abs.x - group.x, y: abs.y - group.y }` | Critical for drag-onto-group (absorption) — confirms the future doc's warning was correct |
| **Floating edges** (`useInternalNode` + `getBezierPath`) | Edge entry/exit points adapt to node position dynamically — no fixed handles | We already have `FloatingEdge` / `ProxyEdge`; confirms the pattern; `useInternalNode` is available if we need to route proxy edges from group boundaries |

---

## What This Iteration Builds

### 1. `NodeToolbar` for the collapse toggle

The `<NodeToolbar />` component from `@xyflow/react` renders a panel attached to a node that:
- Floats above the node at a fixed screen-space size (unscaled by zoom)
- Can be always visible or conditional (`isVisible` prop)
- Does not interfere with node drag (it's outside the node DOM)

We use it to place a single ▼/▶ collapse toggle on every `GroupNode`. No `nodrag` class needed because the toolbar is not inside the node body.

```tsx
<NodeToolbar position={Position.Top} align="start" isVisible>
  <button onClick={toggleCollapse}>{collapsed ? '▶' : '▼'}</button>
</NodeToolbar>
```

### 2. `node.hidden` + `edge.hidden` for child visibility

React Flow's native `hidden` property on nodes and edges suppresses rendering without removing items from state. This means:

- Children stay in `nodes` array — no state loss on expand
- Edges stay in `edges` array — relation types, focus behavior, undo stack all unaffected
- No changes to `displayNodes` or `displayEdges` computation required

Collapsing a group:
```ts
setNodes(all => all.map(n =>
  n.parentId === groupId ? { ...n, hidden: true } : n
));
setEdges(all => all.map(e =>
  childIds.has(e.source) || childIds.has(e.target) ? { ...e, hidden: true } : e
));
```

Expanding reverses `hidden: false`.

### 3. `useReactFlow()` + `useNodeId()` inside `GroupNode`

Instead of threading a callback from `NodeEditorInner` through `node.data`, `GroupNode` uses:
- `useNodeId()` — gets its own ID without any prop
- `useReactFlow()` — direct access to `setNodes`, `setEdges`, `getNodes`

The component is fully self-contained.

```tsx
const id = useNodeId();
const { setNodes, setEdges, getNodes } = useReactFlow();

const toggleCollapse = useCallback(() => {
  const childIds = new Set(
    getNodes().filter(n => n.parentId === id).map(n => n.id)
  );
  const next = !collapsed;
  setNodes(all => all.map(n =>
    n.parentId === id ? { ...n, hidden: next } :
    n.id === id ? { ...n, data: { ...n.data, collapsed: next } } : n
  ));
  setEdges(all => all.map(e =>
    childIds.has(e.source) || childIds.has(e.target)
      ? { ...e, hidden: next }
      : e
  ));
}, [collapsed, id, getNodes, setNodes, setEdges]);
```

### 4. Proxy edges

When a group is collapsed, its children's edges are hidden — so connections to/from children become invisible. We replace them with **proxy edges**: edges from/to the group node itself, deduplicated by `source+target`.

Proxy edges are computed and injected when collapsing, removed when expanding. They are stored as regular edges with `data.relationType: 'proxy'` and a dashed style.

```ts
// On collapse: compute proxy edges
const proxyEdges = deduplicateByEndpoints(
  allEdges
    .filter(e => childIds.has(e.source) || childIds.has(e.target))
    .map(e => ({
      ...e,
      id: `proxy:${groupId}:${e.id}`,
      source: childIds.has(e.source) ? groupId : e.source,
      target: childIds.has(e.target) ? groupId : e.target,
      data: { ...e.data, relationType: 'proxy' },
      style: { strokeDasharray: '4 3', opacity: 0.5 },
    }))
);

// On expand: remove proxy edges
setEdges(all => all.filter(e => !e.id.startsWith(`proxy:${groupId}:`)));
```

### 5. `NodeResizer` for automatic dimension management

From the selection-grouping example: `<NodeResizer />` inside a group node automatically adjusts the group's dimensions as children are added/removed. On collapse we override width/height to a compact fixed size; on expand we restore by removing the override and letting `NodeResizer` re-fit. This replaces manually tracking and restoring `style.height`.

```tsx
<NodeResizer isVisible={selected} minWidth={160} minHeight={40} />
```

### 6. `useOnSelectionChange()` — bonus: group selected nodes

Not needed for collapse/expand but unlocked by this iteration: we can add a "Group selected" action to the editor using `useOnSelectionChange()` to detect multi-node selection and `<NodeToolbar />` to surface the button. Deferred to its own task.

### 7. `dragHandle` — not needed

`NodeToolbar` renders outside the node DOM so it doesn't intercept drag. No `dragHandle` prop change required.

### 8. Drag-onto-group (absorption) — deferred

From the parent-child example: when a dragged node's center falls inside a group, set `parentId` and convert absolute → parent-relative coordinates: `child.position = { x: abs.x - group.x, y: abs.y - group.y }`. The coordinate transform is non-trivial. **Out of scope for this iteration.**

### 9. `useExpandCollapse` reference hook

The official ReactFlow expand-collapse example ships a `useExpandCollapse` hook that manages the full graph in memory and computes visible subsets with Dagre layout recalculation. We adapt its pattern rather than copy it directly (our graph is not a tree). The key insight: keep the full graph in `nodes`/`edges` state always; compute the visible subset reactively using `hidden` flags.

---

## GroupNode Changes (summary)

**Before:**
- Dashed border container, label above, no header, no interaction

**After:**
- `NodeToolbar` at top-left with ▶/▼ toggle (always visible)
- Label + child count badge inside the toolbar
- Collapsed state: group node shrinks to a compact card (`style.height` set to fixed small value), children hidden, proxy edges injected
- Expanded state: group node restores original `style`, children unhidden, proxy edges removed

---

## What We Are NOT Building (future scope)

| Feature | Why deferred |
|---|---|
| `collapse_behavior: summary \| hide` from schema | Hardcode `summary` for now |
| elkjs compound layout | Dagre + `NodeResizer` is sufficient |
| Zustand store / unified state contract | `useReactFlow` + local state is sufficient |
| Collapse as undoable action | Borderline per future doc; deferred |
| 3-level nesting depth cap | Not needed yet |
| Absorption via drag (parent-child reparenting) | Coordinate transform complexity — separate iteration |
| "Group selected nodes" action | Enabled by `useOnSelectionChange` — separate task |
| `useInternalNode` for proxy edge routing from group boundary | Only needed if floating edges need to originate at group perimeter |

---

## Definition of Done

- [ ] GroupNode has a visible collapse toggle (`NodeToolbar`, always visible)
- [ ] `useNodeId()` used inside GroupNode — no prop threading for ID
- [ ] Clicking toggle hides/shows children via `node.hidden`
- [ ] Child edges hidden via `edge.hidden` when collapsed
- [ ] Proxy edges (dashed, `relationType: 'proxy'`) appear from group node to external nodes when collapsed
- [ ] Proxy edges removed on expand
- [ ] Child count badge shown in toolbar
- [ ] `NodeResizer` manages group dimensions; collapsed state overrides to compact fixed size
- [ ] Toggle works in both `readOnly` and edit modes
- [ ] No regressions on `/cv` or `/graph` pages
