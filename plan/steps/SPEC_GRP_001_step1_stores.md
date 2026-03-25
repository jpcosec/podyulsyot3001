# Step 1: Zustand Stores (State Management)

**Spec:** SPEC_GRP_001  
**Phase:** 1 (Data Foundation)  
**Priority:** HIGH — All subsequent steps depend on stores

---

## 1. Migration Notes

> Not applicable — stores are new code. No legacy component to extract. This step creates the state container that holds all graph data.

**Why new?**
- Current `KnowledgeGraph.tsx` uses `useState` + `useNodesState` + `useEdgesState` from ReactFlow
- Blueprint mandates Zustand with atomic selectors to avoid unnecessary re-renders
- Undo/redo must be semantic (action-based), not visual state snapshots

---

## 2. Data Contract

### Graph Store

```ts
interface ASTNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    typeId: string;
    payload: Record<string, unknown>;
    properties: Record<string, string>;
    visualToken?: string;
  };
  parentId?: string;
  hidden?: boolean;
}

interface ASTEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  data?: {
    relationType: string;
    properties: Record<string, string>;
    _originalSource?: string;
    _originalTarget?: string;
  };
  hidden?: boolean;
}
```

### UI Store

```ts
type EditorState = 'browse' | 'focus' | 'edit_node' | 'edit_relation';

interface FilterState {
  hiddenRelationTypes: string[];
  filterText: string;
  attributeFilter: { key: string; value: string } | null;
  hideNonNeighbors: boolean;
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── stores/
│   ├── types.ts              # Shared types (ASTNode, ASTEdge, SemanticAction)
│   ├── graph-store.ts        # nodes, edges, history, dirty
│   └── ui-store.ts           # editorState, focusedId, filters, sidebar
```

---

## 4. Implementation

### stores/types.ts

```ts
// Core types for graph state

export interface ASTNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    typeId: string;
    payload: Record<string, unknown>;
    properties: Record<string, string>;
    visualToken?: string;
  };
  parentId?: string;
  hidden?: boolean;
}

export interface ASTEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  data?: {
    relationType: string;
    properties: Record<string, string>;
    _originalSource?: string;
    _originalTarget?: string;
  };
  hidden?: boolean;
}

export interface SemanticAction {
  type: 'CREATE_ELEMENTS' | 'DELETE_ELEMENTS' | 'UPDATE_NODE' | 'UPDATE_EDGE';
  payload: unknown;
  timestamp: number;
  actor?: string;
  affectedIds: string[];
}
```

### stores/graph-store.ts

```ts
import { create } from 'zustand';
import type { ASTNode, ASTEdge, SemanticAction } from './types';

interface GraphStore {
  // Data
  nodes: ASTNode[];
  edges: ASTEdge[];
  
  // History (semantic, not visual)
  undoStack: SemanticAction[];
  redoStack: SemanticAction[];
  
  // Dirty state
  savedSnapshot: string | null;
  
  // Queries
  isDirty: () => boolean;
  
  // Mutations
  addElements: (nodes: ASTNode[], edges: ASTEdge[]) => void;
  removeElements: (nodeIds: string[], edgeIds: string[]) => void;
  updateNode: (nodeId: string, patch: Partial<ASTNode>) => void;
  updateEdge: (edgeId: string, patch: Partial<ASTEdge>) => void;
  
  // History
  undo: () => void;
  redo: () => void;
  
  // Persistence
  loadGraph: (nodes: ASTNode[], edges: ASTEdge[]) => void;
  markSaved: () => void;
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  nodes: [],
  edges: [],
  undoStack: [],
  redoStack: [],
  savedSnapshot: null,
  
  isDirty: () => {
    const { nodes, edges, savedSnapshot } = get();
    const current = JSON.stringify({ nodes, edges });
    return current !== savedSnapshot;
  },
  
  addElements: (nodes, edges) => {
    const action: SemanticAction = {
      type: 'CREATE_ELEMENTS',
      payload: { nodes, edges },
      timestamp: Date.now(),
      affectedIds: [...nodes.map(n => n.id), ...edges.map(e => e.id)],
    };
    set(state => ({
      nodes: [...state.nodes, ...nodes],
      edges: [...state.edges, ...edges],
      undoStack: [action, ...state.undoStack],
      redoStack: [],
    }));
  },
  
  removeElements: (nodeIds, edgeIds) => {
    const { nodes, edges } = get();
    const nodesToRemove = nodes.filter(n => nodeIds.includes(n.id));
    const edgesToRemove = edges.filter(e => edgeIds.includes(e.id));
    const action: SemanticAction = {
      type: 'DELETE_ELEMENTS',
      payload: { nodes: nodesToRemove, edges: edgesToRemove },
      timestamp: Date.now(),
      affectedIds: [...nodeIds, ...edgeIds],
    };
    set(state => ({
      nodes: state.nodes.filter(n => !nodeIds.includes(n.id)),
      edges: state.edges.filter(e => !edgeIds.includes(e.id)),
      undoStack: [action, ...state.undoStack],
      redoStack: [],
    }));
  },
  
  updateNode: (nodeId, patch) => {
    const { nodes } = get();
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    const updatedNode = { ...node, ...patch };
    const action: SemanticAction = {
      type: 'UPDATE_NODE',
      payload: { before: node, after: updatedNode },
      timestamp: Date.now(),
      affectedIds: [nodeId],
    };
    set(state => ({
      nodes: state.nodes.map(n => n.id === nodeId ? updatedNode : n),
      undoStack: [action, ...state.undoStack],
      redoStack: [],
    }));
  },
  
  updateEdge: (edgeId, patch) => {
    const { edges } = get();
    const edge = edges.find(e => e.id === edgeId);
    if (!edge) return;
    const updatedEdge = { ...edge, ...patch };
    const action: SemanticAction = {
      type: 'UPDATE_EDGE',
      payload: { before: edge, after: updatedEdge },
      timestamp: Date.now(),
      affectedIds: [edgeId],
    };
    set(state => ({
      edges: state.edges.map(e => e.id === edgeId ? updatedEdge : e),
      undoStack: [action, ...state.undoStack],
      redoStack: [],
    }));
  },
  
  undo: () => {
    const { undoStack } = get();
    const action = undoStack[0];
    if (!action) return;
    
    // Reverse action based on type
    const { nodes, edges } = get();
    let newNodes = nodes;
    let newEdges = edges;
    
    switch (action.type) {
      case 'CREATE_ELEMENTS': {
        const payload = action.payload as { nodes: ASTNode[]; edges: ASTEdge[] };
        newNodes = nodes.filter(n => !payload.nodes.some(pn => pn.id === n.id));
        newEdges = edges.filter(e => !payload.edges.some(pe => pe.id === e.id));
        break;
      }
      case 'DELETE_ELEMENTS': {
        const payload = action.payload as { nodes: ASTNode[]; edges: ASTEdge[] };
        newNodes = [...payload.nodes, ...nodes];
        newEdges = [...payload.edges, ...edges];
        break;
      }
      case 'UPDATE_NODE': {
        const payload = action.payload as { before: ASTNode; after: ASTNode };
        newNodes = nodes.map(n => n.id === payload.after.id ? payload.before : n);
        break;
      }
      case 'UPDATE_EDGE': {
        const payload = action.payload as { before: ASTEdge; after: ASTEdge };
        newEdges = edges.map(e => e.id === payload.after.id ? payload.before : e);
        break;
      }
    }
    
    set({
      nodes: newNodes,
      edges: newEdges,
      undoStack: undoStack.slice(1),
      redoStack: [action, ...get().redoStack],
    });
  },
  
  redo: () => {
    const { redoStack } = get();
    const action = redoStack[0];
    if (!action) return;
    
    // Re-apply action
    const { nodes, edges } = get();
    let newNodes = nodes;
    let newEdges = edges;
    
    switch (action.type) {
      case 'CREATE_ELEMENTS': {
        const payload = action.payload as { nodes: ASTNode[]; edges: ASTEdge[] };
        newNodes = [...nodes, ...payload.nodes];
        newEdges = [...edges, ...payload.edges];
        break;
      }
      case 'DELETE_ELEMENTS': {
        const payload = action.payload as { nodes: ASTNode[]; edges: ASTEdge[] };
        newNodes = nodes.filter(n => !payload.nodes.some(pn => pn.id === n.id));
        newEdges = edges.filter(e => !payload.edges.some(pe => pe.id === e.id));
        break;
      }
      case 'UPDATE_NODE': {
        const payload = action.payload as { before: ASTNode; after: ASTNode };
        newNodes = nodes.map(n => n.id === payload.before.id ? payload.after : n);
        break;
      }
      case 'UPDATE_EDGE': {
        const payload = action.payload as { before: ASTEdge; after: ASTEdge };
        newEdges = edges.map(e => e.id === payload.before.id ? payload.after : e);
        break;
      }
    }
    
    set({
      nodes: newNodes,
      edges: newEdges,
      redoStack: redoStack.slice(1),
      undoStack: [action, ...get().undoStack],
    });
  },
  
  loadGraph: (nodes, edges) => {
    const snapshot = JSON.stringify({ nodes, edges });
    set({ 
      nodes, 
      edges, 
      savedSnapshot: snapshot,
      undoStack: [],
      redoStack: [],
    });
  },
  
  markSaved: () => {
    const { nodes, edges } = get();
    const snapshot = JSON.stringify({ nodes, edges });
    set({ savedSnapshot: snapshot });
  },
}));
```

### stores/ui-store.ts

```ts
import { create } from 'zustand';

type EditorState = 'browse' | 'focus' | 'edit_node' | 'edit_relation';

interface FilterState {
  hiddenRelationTypes: string[];
  filterText: string;
  attributeFilter: { key: string; value: string } | null;
  hideNonNeighbors: boolean;
}

interface UIStore {
  editorState: EditorState;
  focusedNodeId: string | null;
  focusedEdgeId: string | null;
  sidebarOpen: boolean;
  filters: FilterState;
  copiedNodeId: string | null;
  
  setEditorState: (state: EditorState) => void;
  setFocusedNode: (id: string | null) => void;
  setFocusedEdge: (id: string | null) => void;
  toggleSidebar: () => void;
  setFilter: (patch: Partial<FilterState>) => void;
  clearFilters: () => void;
  copyNode: (id: string) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  editorState: 'browse',
  focusedNodeId: null,
  focusedEdgeId: null,
  sidebarOpen: true,
  filters: {
    hiddenRelationTypes: [],
    filterText: '',
    attributeFilter: null,
    hideNonNeighbors: true,
  },
  copiedNodeId: null,
  
  setEditorState: (editorState) => set({ editorState }),
  setFocusedNode: (focusedNodeId) => set({ focusedNodeId }),
  setFocusedEdge: (focusedEdgeId) => set({ focusedEdgeId }),
  toggleSidebar: () => set(state => ({ sidebarOpen: !state.sidebarOpen })),
  setFilter: (patch) => set(state => ({ filters: { ...state.filters, ...patch } })),
  clearFilters: () => set({ 
    filters: { 
      hiddenRelationTypes: [], 
      filterText: '', 
      attributeFilter: null, 
      hideNonNeighbors: true 
    } 
  }),
  copyNode: (copiedNodeId) => set({ copiedNodeId }),
}));
```

---

## 5. Styles (Terran Command)

No styles — stores are pure logic. No UI components yet.

---

## 6. Definition of Done

```
[ ] stores/types.ts exports ASTNode, ASTEdge, SemanticAction interfaces
[ ] graph-store.ts exports useGraphStore with all methods
[ ] graph-store.isDirty() returns true after mutations, false after markSaved()
[ ] graph-store.undo() reverses last action correctly
[ ] graph-store.redo() re-applies undone action correctly
[ ] ui-store.ts exports useUIStore with all methods
[ ] ui-store.setFilter() merges partial filter updates
[ ] No TypeScript errors
[ ] No console errors on import
```

---

## 7. E2E (TestSprite)

Not applicable — stores are logic layer, tested via component integration in later steps.

---

## 8. Git Workflow

### Commit

```
feat(stores): implement Zustand stores (GRP-001-01)

- stores/types.ts with ASTNode, ASTEdge, SemanticAction
- stores/graph-store.ts with nodes, edges, undo/redo, isDirty
- stores/ui-store.ts with editorState, filters, focusedId
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-01: Zustand stores for state management.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `zustand` | State management with atomic selectors (per Guide) |

Install: `npm install zustand` (already in blueprint dependencies)

---

## 10. Next Step

GRP-001-02 — Schema Translation (schemaToGraph, graphToDomain) — work with real data from stores.