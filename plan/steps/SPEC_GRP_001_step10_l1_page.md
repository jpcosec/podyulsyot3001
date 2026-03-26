# Step 10: L1 GraphEditorPage (Orchestrator)

**Spec:** SPEC_GRP_001  
**Phase:** 4 (Integration)  
**Priority:** HIGH — Brings all previous steps together  
**Dependencies:** 
- GRP-001-00 (prerequisites: data provider is defined)
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

**Blocking requirement:** this step must not reference undefined modules. If `@/mock/client` does not exist yet, define a data provider first or use documented fetch endpoints.

---

## 2. Data Contract

### Input: From API/Mock

```ts
// Schema JSON (defines available node types)
interface SchemaJSON {
  node_types: Array<{
    id: string;
    display_name: string;
    visual: {
      color_token: string;
      icon: string;
    };
    attributes: Record<string, { type: string; required: boolean }>;
  }>;
}

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
│   ├── lib/
│   │   └── data-provider.ts       # Real API or mock-backed provider
│   └── L2-canvas/
│       └── GraphEditor.tsx       # Container (L2 - owns sidebar, panels)
```

---

## 4. Implementation

### features/graph-editor/L1-app/GraphEditorPage.tsx

```tsx
import { useMemo, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { GraphEditor } from '../L2-canvas/GraphEditor';
import { useGraphStore } from '@/stores/graph-store';
import { registry } from '@/schema/registry';
import { schemaToGraph } from '../lib/schema-to-graph';
import { graphToDomain } from '../lib/graph-to-domain';
import { graphDataProvider } from '@/features/graph-editor/lib/data-provider';
import { z } from 'zod';

// Placeholder renderers - will be connected to real L3 components after Step 4
const PlaceholderDot = ({ colorToken }: { colorToken: string }) => (
  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
);
const PlaceholderLabel = ({ title }: { title: string }) => (
  <span className="text-xs">{title}</span>
);
const PlaceholderDetail = (props: any) => (
  <div className="p-2 min-w-[150px] border rounded">
    <p className="text-xs font-semibold">{props.title || 'Untitled'}</p>
    <p className="text-[10px] text-muted-foreground">Loading...</p>
  </div>
);

export function GraphEditorPage() {
  const loadGraph = useGraphStore(s => s.loadGraph);
  const isDirty = useGraphStore(s => s.isDirty);
  
  // Fetch schema JSON first (defines node types)
  const { data: schemaData, isLoading: schemaLoading, error: schemaError } = useQuery({
    queryKey: ['schema'],
    queryFn: () => graphDataProvider.getSchema(),
  });
  
  // Fetch raw graph data
  const { data: rawData, isLoading: dataLoading, error: dataError } = useQuery({
    queryKey: ['graph'],
    queryFn: () => graphDataProvider.getGraph(),
  });
  
  // CRITICAL: Register node types from schema BEFORE rendering L2
  useEffect(() => {
    if (!schemaData?.node_types) return;
    
    // Clear existing registrations (important for hot reload / schema changes)
    registry.getAll().forEach(type => {
      // Note: registry.clear() would remove all - we selectively update
    });
    
    // Register each node type from schema dynamically
    schemaData.node_types.forEach((typeDef: any) => {
      // Build Zod schema from JSON attributes
      const shape: Record<string, z.ZodTypeAny> = {};
      Object.entries(typeDef.attributes || {}).forEach(([key, attr]: [string, any]) => {
        if (attr.type === 'string') {
          shape[key] = attr.required ? z.string().min(1) : z.string().optional();
        } else if (attr.type === 'number') {
          shape[key] = attr.required ? z.number() : z.number().optional();
        }
        // Add more type mappings as needed
      });
      
      registry.register({
        typeId: typeDef.id,
        label: typeDef.display_name,
        icon: typeDef.visual?.icon || 'circle',
        category: typeDef.category || 'entity',
        colorToken: typeDef.visual?.color_token || `token-${typeDef.id}`,
        payloadSchema: z.object(shape),
        renderers: {
          dot: PlaceholderDot,
          label: PlaceholderLabel,
          detail: PlaceholderDetail,
        },
        defaultSize: { width: 180, height: 70 },
        allowedConnections: typeDef.allowed_connections || [],
      });
    });
  }, [schemaData]);
  
  // Save mutation
  const saveMutation = useMutation({
    mutationFn: (domainData: any) => graphDataProvider.saveGraph(domainData),
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
  useEffect(() => {
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
  if (schemaLoading || dataLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="space-y-2">
          <div className="h-12 w-[300px] bg-muted animate-pulse rounded" />
          <div className="h-8 w-[200px] bg-muted animate-pulse rounded" />
          <p className="text-xs text-muted-foreground">Loading schema and graph...</p>
        </div>
      </div>
    );
  }
  
  // Error state
  if (schemaError || dataError) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-destructive text-center">
          <p className="font-medium">Failed to load</p>
          <p className="text-sm text-muted-foreground mt-1">
            {String(schemaError || dataError)}
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

> **IMPORTANT:** This is the ONLY correct approach for production. L1 must:
> 1. Fetch schema JSON (defines available node types)
> 2. Iterate over `schema.node_types`
> 3. Dynamically register each type in the registry
> 4. THEN render L2 (GraphCanvas)
> 
> The old approach (importing `register-defaults.ts`) was ONLY for development/testing.

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
[ ] GraphEditorPage fetches schema JSON first
[ ] Registry is populated dynamically from schema.node_types
[ ] GraphEditorPage fetches graph data via useQuery
[ ] schemaToGraph converts raw data to AST
[ ] AST loaded into store via loadGraph
[ ] handleSave converts AST to domain and mutates
[ ] Loading shows skeleton
[ ] Error shows banner with retry
[ ] GraphEditor (L2) mounts canvas, sidebar, panels
[ ] No register-defaults.ts import in production code
[ ] No TypeScript errors
[ ] Full integration works end-to-end
```

---

## 7. Local Verification

1. Confirm data provider imports resolve (no module-not-found errors).
2. Verify loading and error states render correctly.
3. Verify schema registration occurs before L2 render.
4. Trigger save and confirm `markSaved()` on success.
5. Typecheck touched modules.

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
| `@/schema/registry` | Node type registry (populated dynamically) |
| `@/components/ui/sonner` | Toast notifications |
| `@/features/graph-editor/lib/data-provider` | Prevent phantom import risk |
| `zod` | Schema validation (for building payload schemas) |

---

## 10. Next Step

Next:
- GRP-001-11 (Theming) — xy-theme.css
- UI refinement steps according to explicit dependencies in `SPEC_UI_001.md`
