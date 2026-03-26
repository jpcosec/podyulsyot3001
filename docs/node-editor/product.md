# Product Document — Node Editor (Graph Editor)

> This document describes what the Node Editor is, what a user can do with it, and how to interact with it. Use this as the source of truth for generating E2E test plans (TestSprite).

---

## What it is

The Node Editor is a visual knowledge graph editor. Users create and edit a network of nodes (entities, concepts, documents) and edges (typed relationships between them). The graph is rendered on an interactive canvas using ReactFlow.

The application is a single-page app at `http://127.0.0.1:5173`. The graph editor occupies the full screen minus a narrow left nav (14px icon rail).

---

## Layout

```
┌──┬─────────────────────────────────────────────────────┐
│  │  Canvas (ReactFlow)                   │  Sidebar     │
│  │                                        │  (right,     │
│Nav│  [nodes floating in space]            │  collapsible)│
│   │                                        │              │
│   │  [minimap bottom-right]               │              │
│   │  [zoom controls bottom-left]          │              │
└──┴─────────────────────────────────────────────────────┘
```

**Nav rail** (left, 56px wide): App icon "P2" + Graph icon (active).

**Canvas** (center): Infinite scrollable/zoomable space. Nodes float in 2D. Edges connect them.

**Sidebar** (right, ~320px): Collapsible. Contains accordion sections: Actions, Filters, Creation, View.

**Inspector panels** (slide in from right over canvas): Sheet panels for editing a selected node or edge.

---

## Reference data

The app loads with a vehicles knowledge graph:

**Groups (containers):**
- `Vehículos` (root group, contains: Terrestres, Aéreos, Acuáticos)
- `Terrestres` (sub-group, contains: Autos, Camiones)
- `Aéreos` (sub-group, contains: Aviones, Helicópteros)
- `Acuáticos` (sub-group, contains: Lanchas, Submarinos)

**Nodes (standalone, outside groups):**
- `Rueda` (category: skill)
- `Hélice` (category: skill)
- `Motor` (category: skill)
- `Radar` (category: skill)

**Edges (all type: "uses"):**
- Rueda → Autos, Camiones
- Hélice → Helicópteros, Lanchas
- Motor → Autos, Camiones, Aviones, Helicópteros, Lanchas
- Radar → Aviones, Submarinos

---

## User interactions

### Canvas navigation

| Action | How |
|--------|-----|
| Pan | Click and drag on empty canvas space |
| Zoom in/out | Mouse scroll wheel, or pinch on touch |
| Fit all nodes | Click "Fit View" button in Controls (bottom-left) |
| Zoom to specific % | Controls buttons (bottom-left): +, −, fit |
| See full graph overview | MiniMap (bottom-right corner) |

### Node selection and focus

| Action | How |
|--------|-----|
| Select a node | Click on it — node gets highlighted border |
| Deselect | Click empty canvas space |
| Focus on a node | Click "Focus" button on node hover toolbar, OR sidebar Focus action — canvas zooms to the node and dims non-neighbors |
| Exit focus mode | Click "Exit Focus" button or press Escape |
| Navigate between nodes | Arrow keys when a node is selected |

### Node editing

| Action | How |
|--------|-----|
| Open node editor | Select a node, then click "Edit" in node toolbar, OR double-click the node |
| Edit name | In the Inspector Sheet (slides in from right): text field at top |
| Edit properties | In Inspector Sheet: key-value pairs (string, number, boolean, date inputs) |
| Add a property | Click "+ Add property" button in Inspector |
| Delete a property | Click × next to a property row |
| Save changes | Click "Save" button in Inspector Sheet |
| Discard changes | Click X to close Sheet without saving |

### Node creation

| Action | How |
|--------|-----|
| Open creation palette | Sidebar → "Creation" accordion section |
| Create a node | Drag a node template card from sidebar and drop onto the canvas |
| Create a node via command | Ctrl+K → type node name → select type |
| Create inside a group | Drag and drop onto a group container |

### Edge creation

| Action | How |
|--------|-----|
| Start a connection | Hover over a node → blue handle dots appear at edges → drag from a handle |
| Complete a connection | Drag to a target node handle and release |
| Cancel connection | Drag to empty space and release |
| Connection validation | Invalid connections (incompatible types) show a red handle — connection is blocked |

### Edge editing

| Action | How |
|--------|-----|
| Select an edge | Click on the edge line |
| Open edge editor | Select edge → click edit button that appears (×) on the edge label |
| Edit relation type | In Edge Inspector Sheet: dropdown for relation type |
| Delete edge via button | Hover edge → [×] button appears on edge midpoint → click |

### Deletion

| Action | How |
|--------|-----|
| Delete selected node/edge | Press Delete key (when in browse mode, not editing) |
| Delete via context menu | Right-click node → "Delete" option |
| Confirm deletion | AlertDialog appears: "Delete [name]?" with Cancel/Delete buttons |
| Undo a deletion | Ctrl+Z |

### Undo / Redo

| Action | How |
|--------|-----|
| Undo last action | Ctrl+Z (Mac: Cmd+Z) |
| Redo | Ctrl+Y (Mac: Cmd+Shift+Z) |
| Undo via sidebar | Sidebar → Actions section → Undo button |
| Redo via sidebar | Sidebar → Actions section → Redo button |

Undoable: create node, delete node, edit node, create edge, delete edge.
NOT undoable: pan, zoom, fit view.

### Save

| Action | How |
|--------|-----|
| Save graph | Ctrl+S, or Sidebar → Actions → Save button |
| Unsaved indicator | Page title shows "•" prefix or save button is highlighted when there are unsaved changes |

### Filters

All filters live in Sidebar → "Filters" accordion section.

| Filter | How |
|--------|-----|
| Text search | Type in search box → nodes not matching are dimmed |
| Filter by relation type | Toggle checkboxes for each relation type ("uses", "contains", etc.) — unchecked types are hidden |
| Filter by attribute | Select attribute key + enter value → only matching nodes visible |
| Show only neighbors | Toggle "Neighbors only" — when a node is focused, hides all non-adjacent nodes |
| Clear all filters | "Clear filters" button |

### Layout

| Action | How |
|--------|-----|
| Auto-layout | Sidebar → View → "Auto Layout" button — runs elkjs and repositions all nodes |
| Manual position | Drag any node to reposition it |
| Save layout | Auto-saved with graph on Save |

### Groups (collapse / expand)

| Action | How |
|--------|-----|
| Collapse a group | Click the collapse toggle (chevron) on the group header |
| Expand a group | Click the expand toggle on the collapsed group header |
| Collapsed state | Group shrinks to header only; edges from child nodes are shown as dashed lines connecting to the group boundary (Edge Inheritance) |
| Move a group | Drag the group header — child nodes move with it |
| Add node to group | Drag node and drop onto a group container |

### Copy / Paste

| Action | How |
|--------|-----|
| Copy a node | Select node → Ctrl+C |
| Paste | Ctrl+V → copy appears offset from original |

### Context menu (right-click)

Right-click on a node shows:
- Focus
- Edit
- Duplicate
- Delete
- Add child node

Right-click on empty canvas:
- Create node (opens creation palette at cursor position)

### Keyboard shortcuts summary

| Shortcut | Action |
|----------|--------|
| Delete | Delete selected element |
| Ctrl+Z / Cmd+Z | Undo |
| Ctrl+Y / Cmd+Shift+Z | Redo |
| Ctrl+C / Cmd+C | Copy selected node |
| Ctrl+V / Cmd+V | Paste |
| Ctrl+S / Cmd+S | Save |
| Ctrl+K / Cmd+K | Open command palette |
| Enter | Enter edit mode on selected node |
| Escape | Exit edit mode / close panels / exit focus |
| Arrow keys | Navigate between nodes (browse mode) |

---

## Modes

The editor has two keyboard modes:

**Browse mode** (default): Canvas owns keyboard. Arrow keys navigate nodes. Delete removes. Enter opens edit mode.

**Edit mode** (when a node inspector is open): The Inspector Sheet owns the keyboard. Typing goes into form fields. Escape returns to browse mode.

---

## URL

- App: `http://127.0.0.1:5173`
- Graph editor: `http://127.0.0.1:5173` (single-page, no sub-routes currently)

---

## Visual style (Terran Command)

The app uses a dark tactical aesthetic:

- Background: `bg-background` (near-black)
- Surfaces: `bg-surface` (dark grey), `bg-surface-high` (slightly lighter)
- Primary accent: cyan/teal (`text-primary`, `border-primary`)
- Text: `text-on-surface` (light grey)
- Typography: `font-mono`, small sizes (`text-[11px]`), uppercase with letter-spacing for labels
- Node borders: colored by category (each node type has a distinct color token)
- Selected nodes: bright cyan border
- Inherited (collapsed) edges: dashed stroke, reduced opacity
