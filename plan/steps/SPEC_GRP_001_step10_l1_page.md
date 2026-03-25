# Step 10: L1 GraphEditorPage (Orchestrator)

**Spec:** SPEC_GRP_001  
**Phase:** 4 (Integration)  
**Priority:** HIGH — Brings all previous steps together  
**Dependencies:** 
- GRP-001-01 (stores)
- GRP-001-02 (schema translation)
- GRP-001-05 (GraphCanvas)
- GRP-001-07 (Sidebar)
- GRP-001-08 (Panels)
- GRP-001-09 (Hooks)

---

## 1. Migration Notes

> Not applicable — L1/L2 split is new architecture. No legacy component to extract.

**Why this step exists:**
- Blueprint: "L1 — App (Router + Data Loader)" and "L2 — Canvas (El editor completo)"
- Current KnowledgeGraph.tsx is one giant L1+L2+L3 combined component
- Per Guide: "L1 es delgado. Decide qué abrir, carga los datos, traduce schema→AST, y renderiza el editor correspondiente."

---

## 2. Data Contract

### Input: From API/Mock

```ts
// Raw data from API
interface RawData {
  nodes: RawNode[];
  edges: RawEdge[];
}
```

### Output: To L2

```ts
interface GraphEditorProps {
  initialNodes: ASTNode[];
  initialEdges: ASTEdge[];
  onSave: () => void;
}
```

### Internal: Store Operations

```ts
// loadGraph: (nodes: ASTNode[], edges: ASTEdge[]) => void
// markSaved: () => void
// isDirty: () => boolean
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   ├── L1-app/
│   │   └── GraphEditorPage.tsx   # Orchestrator (thin L1)
│   └── L2-canvas/
│       └── GraphEditor.tsx       # Container (L2 - owns sidebar, panels)
```

---

## 4. Implementation

### features/graph-editor/L1-app/GraphEditorPage.tsx

```tsx
import { useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { GraphEditor } from '../L2-canvas/GraphEditor';
import { useGraphStore } from '@/stores/graph-store';
import { schemaToGraph } from '../lib/schema-to-graph';
import { graphToDomain } from '../lib/graph-to-domain';
import { mockClient } from '@/mock/client';

// Load registry defaults (registers node types)
import '@/schema/register-defaults';

export function GraphEditorPage() {
  const loadGraph = useGraphStore(s => s.loadGraph);
  const isDirty = useGraphStore(s => s.isDirty);
  
  // Fetch raw data from API
  const { data: rawData, isLoading, error } = useQuery({
    queryKey: ['graph'],
    queryFn: () => mockClient.getGraph(),
  });
  
  // Save mutation
  const saveMutation = useMutation({
    mutationFn: (domainData: any) => mockClient.saveGraph(domainData),
    onSuccess: () => {
      useGraphStore.getState().markSaved();
    },
    onError: () => {
      // Error handling via toast (Sonner)
    },
  });
  
  // Translate schema to AST
  const { nodes, edges } = useMemo(() => {
    if (!rawData) return { nodes: [], edges: [] };
    const ast = schemaToGraph(rawData);
    return { nodes: ast.nodes, edges: ast.edges };
  }, [rawData]);
  
  // Load into store on initial render
  useMemo(() => {
    if (nodes.length > 0) {
      loadGraph(nodes, edges);
    }
  }, [nodes, edges, loadGraph]);
  
  // Save handler
  const handleSave = () => {
    const currentNodes = useGraphStore.getState().nodes;
    const currentEdges = useGraphStore.getState().edges;
    const domainData = graphToDomain(currentNodes, currentEdges);
    saveMutation.mutate(domainData);
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="space-y-2">
          <div className="h-12 w-[300px] bg-muted animate-pulse rounded" />
          <div className="h-8 w-[200px] bg-muted animate-pulse rounded" />
          <p className="text-xs text-muted-foreground">Loading graph...</p>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-destructive text-center">
          <p className="font-medium">Failed to load graph</p>
          <p className="text-sm text-muted-foreground mt-1">
            {String(error)}
          </p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 text-sm underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  
  // L1 delegates to L2. L2 owns sidebar, panels, controls.
  return (
    <GraphEditor
      initialNodes={nodes}
      initialEdges={edges}
      onSave={handleSave}
    />
  );
}
```

### features/graph-editor/L2-canvas/GraphEditor.tsx

```tsx
import { GraphCanvas } from './GraphCanvas';
import { CanvasSidebar } from './sidebar/CanvasSidebar';
import { NodeInspector } from './panels/NodeInspector';
import { EdgeInspector } from './panels/EdgeInspector';
import { Toaster } from "@/components/ui/sonner";
import { useKeyboard } from './hooks/use-keyboard';

interface GraphEditorProps {
  initialNodes: any[];
  initialEdges: any[];
  onSave: () => void;
}

export function GraphEditor({ onSave }: GraphEditorProps) {
  // Initialize keyboard shortcuts
  useKeyboard();
  
  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Canvas area */}
      <div className="flex-1 relative">
        <GraphCanvas />
      </div>
      
      {/* Sidebar (L2) */}
      <CanvasSidebar />
      
      {/* Inspector panels (L2) */}
      <NodeInspector />
      <EdgeInspector />
      
      {/* Toast notifications */}
      <Toaster />
    </div>
  );
}
```

---

## 5. Styles (Terran Command)

Per Guide: Uses existing layout classes
- `h-screen w-full` — full viewport
- `flex-1` — canvas takes remaining space
- Loading/error states use existing patterns

---

## 6. Definition of Done

```
[ ] GraphEditorPage fetches data via useQuery
[ ] schemaToGraph converts raw data to AST
[ ] AST loaded into store via loadGraph
[ ] handleSave converts AST to domain and mutates
[ ] Loading shows skeleton
[ ] Error shows banner with retry
[ ] GraphEditor (L2) mounts canvas, sidebar, panels
[ ] No TypeScript errors
[ ] Full integration works end-to-end
```

---

## 7. E2E (TestSprite)

1. Navigate to /graph
2. Loading skeleton shows briefly
3. Canvas renders with nodes and edges
4. Drag node → position updates
5. Click node → inspector panel opens
6. Edit properties → changes persist
7. Click Save → toast confirms
8. Press Ctrl+Z → undo works
9. Click sidebar section → accordion expands

---

## 8. Git Workflow

### Commit

```
feat(integration): implement L1 orchestrator and L2 container (GRP-001-10)

- features/graph-editor/L1-app/GraphEditorPage.tsx (thin L1)
- features/graph-editor/L2-canvas/GraphEditor.tsx (L2 container)
- Full integration of all previous steps
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-10: L1/L2 integration (GraphEditorPage + GraphEditor).
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@tanstack/react-query` | Data fetching (per Guide) |
| `@/stores/graph-store` | State management |
| `@/features/graph-editor/lib/*` | Schema translation |
| `@/schema/register-defaults` | Node type registration |
| `@/components/ui/sonner` | Toast notifications |

---

## 10. Next Step

Remaining GRP steps:
- GRP-001-07 (Sidebar) — if not already done
- GRP-001-08 (Panels) — if not already done  
- GRP-001-09 (Hooks) — if not already done
- GRP-001-11 (Theming) — xy-theme.css

Then UI steps can run in parallel.