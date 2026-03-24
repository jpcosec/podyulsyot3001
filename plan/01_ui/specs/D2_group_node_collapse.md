# Spec D2 — Group Node Collapse / Expand

**Feature:** `src/pages/global/KnowledgeGraph.tsx` — `GroupNode` component + collapse logic
**Depends on:** D1 (SchemaExplorer, readOnly mode, CATEGORY_COLORS)
**Libraries:** `@xyflow/react` (NodeToolbar, node.hidden, useReactFlow)

---

## Context

When planning collapse/expand in the future docs (`plan/future/02_structured_documents_and_subflows.md`), the design assumed we would need custom state management, proxy edge computation, and callback threading from the editor shell down to node components.

A review of the ReactFlow API reveals that three built-in primitives make most of that unnecessary:

| ReactFlow feature | What it gives us | Future-doc assumption it replaces |
|---|---|---|
| `NodeToolbar` | Floating, zoom-invariant button panel attached to a node — always legible | Header-inside-node-body with collapse toggle |
| `node.hidden` / `edge.hidden` | Native React Flow property — hidden nodes/edges stay in state but are not rendered | Manual filtering in `displayNodes` / proxy edge construction |
| `useReactFlow()` inside node components | Direct access to `setNodes` / `setEdges` from inside any node | Threading `onToggleCollapse` callback through `node.data` from `NodeEditorInner` |

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

### 3. `useReactFlow()` inside `GroupNode`

Instead of threading a callback from `NodeEditorInner` through `node.data`, `GroupNode` calls `useReactFlow()` directly to access `setNodes` and `setEdges`. The component is self-contained.

```tsx
const { setNodes, setEdges, getNodes } = useReactFlow();

const toggleCollapse = useCallback(() => {
  const childIds = new Set(
    getNodes().filter(n => n.parentId === id).map(n => n.id)
  );
  const next = !collapsed;
  setNodes(all => all.map(n =>
    n.parentId === id ? { ...n, hidden: next } : n
    // also update own data.collapsed flag
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

### 5. `dragHandle` — not needed

`NodeToolbar` renders outside the node DOM so it doesn't intercept drag. The group node body already handles drag correctly. No `dragHandle` prop change required.

### 6. Intersection detection — deferred

`getIntersectingNodes()` could auto-assign `parentId` when dragging a node onto a group. This is the "absorption" interaction from the future docs. **Out of scope for this iteration** — we handle it when drag-to-group is needed.

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

| Future-doc feature | Why deferred |
|---|---|
| `collapse_behavior: summary \| hide` from schema | Hardcode `summary` for now |
| elkjs compound layout | Dagre is sufficient |
| Zustand store / unified state contract | `useState` + `useReactFlow` is sufficient |
| Collapse as undoable action | Borderline per future doc; deferred |
| 3-level nesting depth cap | Not needed yet |
| Absorption via drag (intersection detection) | Separate iteration |

---

## Definition of Done

- [ ] GroupNode has a visible collapse toggle (NodeToolbar)
- [ ] Clicking toggle hides/shows children via `node.hidden`
- [ ] Child edges hidden via `edge.hidden` when collapsed
- [ ] Proxy edges (dashed) appear from group node to external nodes when collapsed
- [ ] Proxy edges removed on expand
- [ ] Child count badge shown in toolbar
- [ ] GroupNode resizes to compact card when collapsed
- [ ] Toggle works in both readOnly and edit modes
- [ ] No regressions on `/cv` or `/graph` pages
