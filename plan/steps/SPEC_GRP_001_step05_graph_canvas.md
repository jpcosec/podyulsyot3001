# Step 5: GraphCanvas (ReactFlow Wrapper + Render Tiers)

**Spec:** SPEC_GRP_001  
**Phase:** 3 (UI Components)  
**Priority:** HIGH — Core canvas, connects stores to ReactFlow  
**Dependencies:** 
- GRP-001-01 (stores)
- GRP-001-03 (registry) 
- GRP-001-04 (L3 components)

**Integration note:** Step 05 can start with temporary edge mapping; finalize custom edge wiring in GRP-001-06.

---

## 1. Migration Notes

> Not applicable — GraphCanvas is new L2 component. No legacy component to extract.

**Why this step exists:**
- Blueprint: "L2-canvas/GraphCanvas.tsx — ReactFlow wrapper"
- Current KnowledgeGraph.tsx has ReactFlow inline (lines 923-1500+)
- This step extracts ReactFlow setup, nodeTypes, edgeTypes into dedicated component
- Per Guide: "Render tiers — contextual zoom con 3 niveles para performance"

---

## 2. Data Contract

### Input: From Store

```ts
// From useGraphStore
nodes: ASTNode[]
edges: ASTEdge[]

// From useUIStore
editorState: 'browse' | 'focus' | 'edit_node' | 'edit_relation'
focusedNodeId: string | null
```

### Output: To ReactFlow

```ts
// ReactFlow node props
interface NodeProps {
  id: string;
  type: 'node' | 'group';
  position: { x: number; y: number };
  data: {
    typeId: string;
    payload: NodePayload;
    properties: Record<string, string>;
    visualToken?: string;
    collapsed?: boolean;
  };
  selected?: boolean;
  parentId?: string;
}

// ReactFlow edge props
interface EdgeProps {
  id: string;
  source: string;
  target: string;
  type: 'floating' | 'button';
  data?: { relationType: string; ... };
  selected?: boolean;
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/L2-canvas/
│   ├── GraphCanvas.tsx       # Main ReactFlow wrapper
│   ├── NodeShell.tsx        # Base node with render tiers
│   ├── GroupShell.tsx       # Collapsible group node
│   └── index.ts             # Export barrel
```

---

## 4. Implementation

### features/graph-editor/L2-canvas/GraphCanvas.tsx

```tsx
import { useCallback, useMemo } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap, 
  Panel,
  useReactFlow,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';
import { NodeShell } from './NodeShell';
import { GroupShell } from './GroupShell';
import { FloatingEdge } from './edges/FloatingEdge';
import { ButtonEdge } from './edges/ButtonEdge';
import { useConnectionValidation } from './hooks/use-connection-validation';
import { ViewControls } from './sidebar/ViewControls';
import type { ASTNode, ASTEdge } from '@/stores/types';

const nodeTypes = {
  node: NodeShell,
  group: GroupShell,
};

const edgeTypes = {
  floating: FloatingEdge,
  button: ButtonEdge,
};

export function GraphCanvas() {
  const nodes = useGraphStore(s => s.nodes);
  const edges = useGraphStore(s => s.edges);
  const updateNode = useGraphStore(s => s.updateNode);
  const updateEdge = useGraphStore(s => s.updateEdge);
  const addElements = useGraphStore(s => s.addElements);
  
  const { fitView } = useReactFlow();
  const isValidConnection = useConnectionValidation();
  const removeElements = useGraphStore(s => s.removeElements);
  
  // Handle node position changes in a controlled canvas.
  // During drag: visual updates only (no undo pollution).
  // On drag end: semantic update for undo/redo.
  const onNodesChange: OnNodesChange = useCallback((changes) => {
    changes.forEach(change => {
      if (change.type === 'position' && change.position) {
        updateNode(
          change.id,
          { position: change.position },
          { isVisualOnly: Boolean(change.dragging) },
        );
      }
    });
  }, [updateNode]);
  
  // Handle edge changes
  const onEdgesChange: OnEdgesChange = useCallback((changes) => {
    changes.forEach(change => {
      if (change.type === 'remove') {
        // ReactFlow handles internal removal; store sync via onEdgesDelete
      }
    });
  }, []);
  
  // Handle node deletion (ReactFlow's built-in delete triggers this)
  const onNodesDelete = useCallback((deletedNodes: ASTNode[]) => {
    const nodeIds = deletedNodes.map(n => n.id);
    // Get edge IDs connected to deleted nodes
    const connectedEdgeIds = edges
      .filter(e => nodeIds.includes(e.source) || nodeIds.includes(e.target))
      .map(e => e.id);
    removeElements(nodeIds, connectedEdgeIds);
  }, [edges, removeElements]);
  
  // Handle edge deletion
  const onEdgesDelete = useCallback((deletedEdges: ASTEdge[]) => {
    const edgeIds = deletedEdges.map(e => e.id);
    removeElements([], edgeIds);
  }, [removeElements]);
  
  // Handle new connections
  const onConnect: OnConnect = useCallback((connection) => {
    if (!connection.source || !connection.target) return;
    
    const newEdge: ASTEdge = {
      id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
      source: connection.source,
      target: connection.target,
      type: 'floating',
      data: {
        relationType: 'linked',
        properties: {},
      },
    };
    
    addElements([], [newEdge]);
  }, [addElements]);
  
  // Filter nodes based on UI state
  const editorState = useUIStore(s => s.editorState);
  const focusedNodeId = useUIStore(s => s.focusedNodeId);
  const filters = useUIStore(s => s.filters);
  
  const displayNodes = useMemo(() => {
    return nodes.map(node => {
      // Text filter
      if (filters.filterText) {
        const name = (node.data.payload.name ?? node.data.payload.title ?? '') as string;
        if (!name.toLowerCase().includes(filters.filterText.toLowerCase())) {
          return { ...node, hidden: true };
        }
      }
      
      // In focus mode, dim non-neighbors
      if (editorState === 'focus' && focusedNodeId) {
        // Logic handled by useEdgeInheritance hook
      }
      
      return node;
    });
  }, [nodes, filters.filterText, editorState, focusedNodeId]);
  
  const displayEdges = useMemo(() => {
    return edges.filter(edge => {
      // Filter by hidden relation types
      if (filters.hiddenRelationTypes.includes(edge.data?.relationType ?? '')) {
        return false;
      }
      return true;
    });
  }, [edges, filters.hiddenRelationTypes]);
  
  return (
    <div className="flex-1 h-full">
      <ReactFlow
        nodes={displayNodes}
        edges={displayEdges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        isValidConnection={isValidConnection}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        onConnect={onConnect}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        defaultEdgeOptions={{
          type: 'floating',
        }}
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap 
          nodeColor={(node) => {
            const typeId = node.data?.typeId;
            return typeId ? `var(--token-${typeId}, #888)` : '#888';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
        <Panel position="top-right" className="m-2">
          <ViewControls />
        </Panel>
      </ReactFlow>
    </div>
  );
}
```

### features/graph-editor/L2-canvas/NodeShell.tsx

```tsx
import { memo, useMemo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { useStore } from 'zustand';
import { registry } from '@/schema/registry';
import { EntityCard } from '@/components/content/EntityCard';
import { PlaceholderNode } from '@/components/content/PlaceholderNode';
import type { ASTNode } from '@/stores/types';

// Render tier thresholds (per Blueprint)
const ZOOM_DETAIL = 0.9;
const ZOOM_LABEL = 0.4;

// Get zoom level from ReactFlow store
const zoomSelector = (s: { transform: [number, number, number] }) => s.transform[2];

export const NodeShell = memo(function NodeShell({ data, selected }: NodeProps<ASTNode>) {
  const zoom = useStore(zoomSelector);
  
  const typeId = data.typeId;
  const def = registry.get(typeId);
  
  // Error node
  if (!def) {
    const errorPayload = data.payload as { typeId: 'error'; message?: string };
    return (
      <div className="border-2 border-red-500 rounded-lg bg-red-50 p-2 min-w-[150px]">
        <span className="text-xs text-red-600">Unknown: {typeId}</span>
        {errorPayload.message && (
          <p className="text-[10px] text-red-400">{errorPayload.message}</p>
        )}
        <Handle type="target" position={Position.Top} />
        <Handle type="source" position={Position.Bottom} />
      </div>
    );
  }
  
  // Determine render tier
  const renderTier: 'dot' | 'label' | 'detail' = useMemo(() => {
    if (zoom >= ZOOM_DETAIL) return 'detail';
    if (zoom >= ZOOM_LABEL) return 'label';
    return 'dot';
  }, [zoom]);
  
  // Get renderer component
  const Renderer = def.renderers[renderTier];
  
  // Build props for renderer - TypeScript infers type from discriminated union
  const title = 'name' in data.payload 
    ? data.payload.name 
    : 'title' in data.payload 
      ? data.payload.title 
      : 'Untitled';
  
  const renderProps = {
    ...data.payload,
    title,
    category: typeId,
    properties: data.properties,
    visualToken: data.visualToken,
  };
  
  return (
    <div
      className={`
        border-2 border-border rounded-lg bg-card
        ${selected ? 'ring-2 ring-primary/40' : ''}
      `}
      style={{ 
        borderColor: `var(--${def.colorToken}, #888)`,
        minWidth: def.defaultSize.width,
      }}
    >
      <Handle 
        type="target" 
        position={Position.Top} 
        className="!bg-muted-foreground !border-muted-foreground"
      />
      
      <Renderer {...renderProps} colorToken={def.colorToken} />
      
      <Handle 
        type="source" 
        position={Position.Bottom}
        className="!bg-muted-foreground !border-muted-foreground"
      />
    </div>
  );
});
```

### features/graph-editor/L2-canvas/GroupShell.tsx

```tsx
import { memo } from 'react';
import { 
  Handle, 
  Position, 
  NodeResizer, 
  NodeToolbar,
  type NodeProps,
} from '@xyflow/react';
import { useGraphStore } from '@/stores/graph-store';
import type { ASTNode } from '@/stores/types';

export const GroupShell = memo(function GroupShell({ data, selected }: NodeProps<ASTNode>) {
  const collapsed = data.collapsed ?? false;
  const updateNode = useGraphStore(s => s.updateNode);
  
  const toggleCollapse = () => {
    updateNode(data.id, { 
      data: { 
        ...data, 
        collapsed: !collapsed 
      }
    });
  };
  
  const groupTitle = 'name' in data.payload 
    ? data.payload.name 
    : 'title' in data.payload 
      ? data.payload.title 
      : 'Group';

  return (
    <>
      <NodeToolbar position={Position.Top} align="start" isVisible>
        <div className="flex items-center gap-2 px-2 py-1 bg-background border rounded text-xs">
          <button 
            onClick={toggleCollapse}
            className="hover:text-primary transition-colors"
          >
            {collapsed ? '▶' : '▼'}
          </button>
          <span className="font-semibold font-headline">
            {groupTitle}
          </span>
        </div>
      </NodeToolbar>
      
      <div
        className={`
          w-full h-full 
          border-2 border-dashed rounded-lg
          bg-transparent
        `}
        style={{ borderColor: `var(--token-section, #666)` }}
      >
        <NodeResizer 
          isVisible={selected && !collapsed} 
          minWidth={160} 
          minHeight={60}
          handleClassName="!bg-primary"
        />
        
        {!collapsed && (
          <>
            <Handle 
              type="target" 
              position={Position.Top}
              className="!bg-muted-foreground !border-muted-foreground"
            />
            <Handle 
              type="source" 
              position={Position.Bottom}
              className="!bg-muted-foreground !border-muted-foreground"
            />
          </>
        )}
      </div>
    </>
  );
});
```

### features/graph-editor/L2-canvas/index.ts

```ts
export { GraphCanvas } from './GraphCanvas';
export { NodeShell } from './NodeShell';
export { GroupShell } from './GroupShell';
```

---

## 5. Styles (Terran Command)

Per Guide: Uses CSS variables from xy-theme.css (created in step 11)
- Node border colors: `var(--token-{typeId})`
- Selected state: `ring-primary/40`
- Background: `bg-card` (shadcn)

---

## 6. Definition of Done

```
[ ] GraphCanvas renders ReactFlow
[ ] NodeShell renders as custom node
[ ] GroupShell renders as group node
[ ] Render tiers work (dot/label/detail based on zoom)
[ ] Node selection works
[ ] Node dragging updates position
[ ] Edge connections create new edges
[ ] isValidConnection uses registry
[ ] onNodesDelete handler syncs to Zustand store
[ ] onEdgesDelete handler syncs to Zustand store
[ ] No unsafe type casts (payload is discriminated union)
[ ] No TypeScript errors
```

---

## 7. Local Verification

1. Load canvas and drag a node: position should update continuously (no frozen drag).
2. Complete drag and run undo: one semantic position action should revert.
3. Connect two nodes and verify new edge in store.
4. Zoom tiers switch between dot/label/detail renderers.

---

## 8. Git Workflow

### Commit

```
feat(canvas): implement GraphCanvas with render tiers (GRP-001-05)

- features/graph-editor/L2-canvas/GraphCanvas.tsx
- features/graph-editor/L2-canvas/NodeShell.tsx (dot/label/detail)
- features/graph-editor/L2-canvas/GroupShell.tsx
- features/graph-editor/L2-canvas/index.ts
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-05: GraphCanvas with ReactFlow, custom node types, render tiers.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@xyflow/react` | ReactFlow canvas (per Guide) |
| `@/stores/graph-store` | State management |
| `@/stores/ui-store` | UI state |
| `@/schema/registry` | Node type definitions |
| `@/components/content/*` | L3 components |

---

## 10. Next Step

GRP-001-06 — Custom Edges (FloatingEdge, ButtonEdge) — edge types referenced in GraphCanvas.
