# Blueprint: Node Editor Refactorizado

> De un God Component de 2,949 líneas a una arquitectura de 3 capas con contratos claros, estado centralizado, y componentes reutilizables.

---

## Estructura de archivos

```
apps/review-workbench/src/
│
├── app/
│   ├── App.tsx                               ← Router + providers
│   └── providers.tsx                         ← QueryClient + ReactFlowProvider + DnDProvider
│
├── stores/
│   ├── graph-store.ts                        ← Zustand: nodes, edges, history, dirty
│   ├── ui-store.ts                           ← Zustand: editorState, focusedId, sidebar, filters
│   └── types.ts                              ← SemanticAction, GraphState, UIState
│
├── schema/
│   ├── registry.ts                           ← Node type registry
│   ├── registry.types.ts                     ← NodeTypeDefinition, PayloadSchema
│   ├── node-types.schema.json                ← Definición de tipos (reemplaza CATEGORY_COLORS + NODE_TEMPLATES)
│   └── validation.ts                         ← Zod schemas para payloads
│
├── components/
│   ├── layouts/
│   │   └── AppShell.tsx                      ← Nav global (logo, links entre páginas)
│   │
│   └── content/                              ← L3: componentes de contenido reutilizables
│       ├── EntityCard.tsx                    ← Título + categoría + badges
│       ├── PropertiesPreview.tsx             ← Tabla key/value colapsable (read-only)
│       ├── PropertyEditor.tsx                ← Input multi-tipo (string, markdown, date, enum, boolean)
│       └── PlaceholderNode.tsx               ← Skeleton para render tiers (zoom-out)
│
├── features/
│   └── graph-editor/
│       │
│       ├── L1-app/                           ← Orquestador: fetch, schema→AST, routing
│       │   └── GraphEditorPage.tsx
│       │
│       ├── L2-canvas/                        ← Editor completo: canvas + controles + sidebar
│       │   ├── GraphCanvas.tsx               ← ReactFlow wrapper
│       │   ├── NodeShell.tsx                 ← BaseNode + render tiers
│       │   ├── GroupShell.tsx                ← LabeledGroupNode + collapse
│       │   ├── InternalNodeRouter.tsx        ← Registry lookup → componente L3
│       │   │
│       │   ├── edges/
│       │   │   ├── FloatingEdge.tsx          ← Ejemplo oficial RF
│       │   │   ├── ButtonEdge.tsx            ← EdgeLabelRenderer + botón [×]
│       │   │   └── edge-helpers.ts           ← getEdgeParams (oficial RF)
│       │   │
│       │   ├── sidebar/
│       │   │   ├── CanvasSidebar.tsx         ← Contenedor con Accordion
│       │   │   ├── ActionsSection.tsx        ← Save, undo, redo, copy, paste, delete
│       │   │   ├── FiltersSection.tsx        ← Relation types, text search, attribute K/V
│       │   │   ├── CreationSection.tsx       ← Template palette + DnD
│       │   │   └── ViewSection.tsx           ← Layout presets, hide non-neighbors
│       │   │
│       │   ├── panels/
│       │   │   ├── NodeInspector.tsx         ← Sheet lateral (shadcn)
│       │   │   └── EdgeInspector.tsx         ← Sheet lateral (shadcn)
│       │   │
│       │   └── xy-theme.css                  ← --xy-* overrides, estados, dark mode
│       │
│       ├── hooks/
│       │   ├── use-graph-layout.ts           ← elkjs wrapper async
│       │   ├── use-edge-inheritance.ts       ← Collapse/expand + reasignación de edges
│       │   ├── use-dnd.ts                    ← Pointer events (patrón RF oficial)
│       │   ├── use-keyboard.ts               ← useKeyPress RF + shortcuts
│       │   └── use-connection-validation.ts  ← isValidConnection desde registry
│       │
│       ├── lib/
│       │   ├── schema-to-graph.ts            ← Pipeline: match → topology → edges
│       │   └── graph-to-domain.ts            ← Serialización inversa (AST → API)
│       │
│       └── types.ts                          ← ASTNode, ASTEdge, contratos L1↔L2
│
├── styles/
│   ├── index.css                             ← @import xy-theme + globals
│   └── styles.css                            ← Tailwind directives + custom utilities
│
└── mock/
    ├── client.ts
    └── fixtures/graph_data.json
```

---

## Definición de capas (corregida)

### L1 — App (Router + Data Loader)

**Pregunta que responde:** "¿Qué documento estoy viendo?"

L1 es delgado. Decide qué abrir, carga los datos, traduce schema→AST, y renderiza el editor correspondiente. Si mañana hay un editor de texto tipo Google Docs, L1 decide cuál mostrar.

**L1 NO contiene:** sidebar, filtros, undo, save, inspectors. Eso es del editor (L2).

| Responsabilidad | Archivo |
|-----------------|---------|
| Fetch de datos (API / mock) | `GraphEditorPage.tsx` |
| Traducir dominio→AST (`schemaToGraph`) | `GraphEditorPage.tsx` vía `lib/schema-to-graph.ts` |
| Decidir qué editor montar | `GraphEditorPage.tsx` |
| Routing entre páginas | `app/App.tsx` |
| Layout global (AppShell) | `components/layouts/AppShell.tsx` |

### L2 — Canvas (El editor completo)

**Pregunta que responde:** "¿Todo lo que hago dentro de un documento?"

L2 es el editor. Si lo sacas y lo pones en otra página, lleva sus propios controles consigo: sidebar, inspectors, undo, save, filtros, creation palette, layout buttons. Es self-contained.

| Responsabilidad | Archivo |
|-----------------|---------|
| Renderizar ReactFlow | `GraphCanvas.tsx` |
| Nodos: cascarón + render tiers | `NodeShell.tsx`, `GroupShell.tsx` |
| Router de contenido L3 | `InternalNodeRouter.tsx` |
| Edges (floating, button) | `edges/` |
| Sidebar del editor | `sidebar/` |
| Inspectors de nodo/edge | `panels/` |
| Layout (elkjs) | `hooks/use-graph-layout.ts` |
| Collapse/expand grupos | `hooks/use-edge-inheritance.ts` |
| DnD sidebar→canvas | `hooks/use-dnd.ts` |
| Keyboard shortcuts | `hooks/use-keyboard.ts` |
| Validación de conexiones | `hooks/use-connection-validation.ts` |
| Tema visual | `xy-theme.css` |

### L3 — Content (Componentes reutilizables)

**Pregunta que responde:** "¿Cómo muestro/edito este dato?"

L3 no sabe que existe un grafo, un canvas, ni un editor. Son componentes React puros con `props` y callbacks. Funcionan en un nodo, en un Sheet lateral, en una tabla, en un modal.

Viven en `components/content/` porque son reutilizables entre features.

| Componente | Props | Callback |
|-----------|-------|----------|
| `EntityCard` | `title`, `category`, `badges` | — |
| `PropertiesPreview` | `properties: Record<string, any>` | — |
| `PropertyEditor` | `pairs: PropertyPair[]`, `attributeTypes` | `onChange(pairs)` |
| `PlaceholderNode` | `title`, `colorToken` | — |

---

## Stores (Zustand)

### graph-store.ts — Estado del grafo + historial semántico

```typescript
import { create } from 'zustand';

interface SemanticAction {
  type: 'CREATE_ELEMENTS' | 'DELETE_ELEMENTS' | 'UPDATE_NODE' | 'UPDATE_EDGE';
  payload: unknown;        // prevState + nextState para undo/redo
  timestamp: number;
  // Preparado para colaboración futura:
  actor?: string;
  affectedIds: string[];
}

interface GraphStore {
  // Data
  nodes: ASTNode[];
  edges: ASTEdge[];

  // History (semántico, no visual)
  undoStack: SemanticAction[];
  redoStack: SemanticAction[];

  // Dirty state
  savedSnapshot: string | null;
  isDirty: () => boolean;

  // Actions (cada una pushea a undoStack)
  addElements: (nodes: ASTNode[], edges: ASTEdge[]) => void;
  removeElements: (nodeIds: string[], edgeIds: string[]) => void;
  updateNode: (nodeId: string, patch: Partial<ASTNode>) => void;
  updateEdge: (edgeId: string, patch: Partial<ASTEdge>) => void;

  // History navigation
  undo: () => void;
  redo: () => void;

  // Persistence
  loadGraph: (nodes: ASTNode[], edges: ASTEdge[]) => void;
  markSaved: () => void;

  // Collapse (edge inheritance)
  collapseGroup: (groupId: string) => void;
  expandGroup: (groupId: string) => void;
}
```

**Reglas:**
- Las acciones son objetos serializables (no closures) → preparado para colaboración
- `undo`/`redo` solo operan sobre acciones semánticas. Pan/zoom no entran aquí.
- `isDirty()` compara serialización actual vs `savedSnapshot`

### ui-store.ts — Estado de la UI del editor

```typescript
interface UIStore {
  // Editor mode
  editorState: 'browse' | 'focus' | 'edit_node' | 'edit_relation';

  // Selection
  focusedNodeId: string | null;
  focusedEdgeId: string | null;

  // Sidebar
  sidebarOpen: boolean;

  // Filters
  hiddenRelationTypes: string[];
  filterText: string;
  attributeFilter: { key: string; value: string } | null;
  hideNonNeighbors: boolean;

  // Clipboard
  copiedNodeId: string | null;

  // Actions
  setEditorState: (state: EditorState) => void;
  setFocusedNode: (id: string | null) => void;
  setFocusedEdge: (id: string | null) => void;
  toggleSidebar: () => void;
  setFilter: (patch: Partial<Filters>) => void;
  clearFilters: () => void;
  copyNode: (id: string) => void;
}
```

**Reglas:**
- Separado de `graph-store` porque el estado de UI no se persiste ni se deshace
- Los componentes L2 usan selectores atómicos: `useUIStore(s => s.focusedNodeId)` — solo re-renderizan cuando su slice cambia

---

## Node Type Registry

```typescript
// schema/registry.ts

interface NodeTypeDefinition {
  typeId: string;
  label: string;
  icon: string;                                    // lucide icon name
  category: string;
  colorToken: string;                              // referencia a xy-theme.css
  payloadSchema: ZodSchema;                        // validación runtime
  sanitizer?: (payload: unknown) => unknown;        // DOMPurify o custom
  renderers: {
    dot: ComponentType<{ colorToken: string }>;                     // zoom < 0.4
    label: ComponentType<{ title: string; icon: string }>;          // zoom 0.4-0.9
    detail: ComponentType<DOMPurifyAny> | LazyExoticComponent<any>; // zoom >= 0.9
  };
  defaultSize: { width: number; height: number };
  allowedConnections: string[];                    // typeIds válidos como target
}

class NodeTypeRegistry {
  private types: Map<string, NodeTypeDefinition>;

  register(def: NodeTypeDefinition): void;
  get(typeId: string): NodeTypeDefinition | undefined;
  getRenderer(typeId: string, zoomLevel: 'dot' | 'label' | 'detail'): ComponentType;
  validatePayload(typeId: string, payload: unknown): ZodSafeParseResult;
  sanitizePayload(typeId: string, payload: unknown): unknown;
  canConnect(sourceTypeId: string, targetTypeId: string): boolean;
}

// Singleton exportado
export const registry = new NodeTypeRegistry();
```

**Reglas:**
- Los `renderers.detail` aceptan `React.lazy()` → bundle splitting gratis
- Si un tipo no registra `sanitizer`, el registry aplica DOMPurify genérico (default deny)
- `payloadSchema` es Zod → valida en runtime lo que TypeScript no puede
- `allowedConnections` alimenta `use-connection-validation.ts`

### Registro de tipos (reemplaza CATEGORY_COLORS + NODE_TEMPLATES)

```typescript
// schema/register-defaults.ts
import { registry } from './registry';
import { EntityCard } from '@/components/content/EntityCard';
import { PlaceholderNode } from '@/components/content/PlaceholderNode';

registry.register({
  typeId: 'person',
  label: 'Person',
  icon: 'user',
  category: 'entity',
  colorToken: 'token-person',
  payloadSchema: z.object({ name: z.string(), role: z.string().optional() }),
  renderers: {
    dot: ({ colorToken }) => <PlaceholderNode colorToken={colorToken} />,
    label: ({ title, icon }) => <NodeLabel title={title} icon={icon} />,
    detail: EntityCard,
  },
  defaultSize: { width: 200, height: 80 },
  allowedConnections: ['skill', 'project', 'publication', 'concept'],
});

// ... skill, project, publication, concept, document, section, entry
```

---

## Contratos entre capas

### L1 → L2: Props del canvas

```typescript
// features/graph-editor/types.ts

interface GraphEditorProps {
  /** AST generado por schemaToGraph() */
  initialNodes: ASTNode[];
  initialEdges: ASTEdge[];

  /** Callback cuando el usuario guarda */
  onSave: (nodes: ASTNode[], edges: ASTEdge[]) => void;

  /** Modo solo lectura */
  readOnly?: boolean;
}
```

L1 pasa datos traducidos. L2 maneja todo lo demás internamente.

### L2 → L3: Via InternalNodeRouter + Registry

```typescript
// L2-canvas/InternalNodeRouter.tsx

function InternalNodeRouter({ typeId, payload, nodeId }: {
  typeId: string;
  payload: unknown;
  nodeId: string;
}) {
  const zoomLevel = useStore(zoomSelector);
  const def = registry.get(typeId);

  if (!def) return <ErrorNode message={`Unknown type: ${typeId}`} />;

  // Validar payload
  const result = def.payloadSchema.safeParse(payload);
  if (!result.success) return <ErrorNode message="Invalid payload" />;

  // Sanitizar
  const clean = def.sanitizePayload
    ? def.sanitizePayload(result.data)
    : defaultSanitize(result.data);

  // Render tier
  const Renderer = def.renderers[zoomLevel];

  return (
    <Suspense fallback={<PlaceholderNode colorToken={def.colorToken} />}>
      <Renderer {...clean} />
    </Suspense>
  );
}
```

No hay contrato formal L2→L3. L3 son componentes React normales. El registry media: valida, sanitiza, y selecciona el renderer correcto.

### L3 → L2: Callbacks simples

```typescript
// Cuando un componente L3 necesita comunicar un cambio:
<PropertyEditor
  pairs={node.properties}
  onChange={(newPairs) => {
    graphStore.updateNode(nodeId, { properties: newPairs });
  }}
/>
```

L3 no importa stores ni hooks del canvas. Recibe `onChange` como prop.

---

## Flujo de datos completo

```
┌─────────────────────────────────────────────────────────────────┐
│ L1: GraphEditorPage                                             │
│   1. useQuery → fetchGraph() → rawData                         │
│   2. schemaToGraph(rawData, schema) → { nodes, edges }         │
│   3. <GraphEditor initialNodes={nodes} initialEdges={edges}    │
│        onSave={(n, e) => mutation.mutate(graphToDomain(n, e))} │
│      />                                                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ ASTNode[], ASTEdge[]
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ L2: GraphCanvas                                                 │
│   graphStore.loadGraph(initialNodes, initialEdges)              │
│                                                                 │
│   ┌──────────┐  ┌────────────────────────────────┐             │
│   │ Sidebar   │  │ ReactFlow                      │             │
│   │ Actions   │  │  nodes ← graphStore.nodes      │             │
│   │ Filters   │  │  edges ← graphStore.edges      │             │
│   │ Creation  │  │  nodeTypes = { node: NodeShell, │             │
│   │ View      │  │              group: GroupShell } │             │
│   └──────────┘  │  edgeTypes = { floating, button }│             │
│                  │                                  │             │
│   ┌──────────┐  │  ┌────────────────────────┐     │             │
│   │Inspector │  │  │ NodeShell               │     │             │
│   │(Sheet)   │  │  │  zoom >= 0.9 → L3      │     │             │
│   │          │  │  │  zoom >= 0.4 → label   │     │             │
│   │          │  │  │  zoom <  0.4 → dot     │     │             │
│   └──────────┘  │  └────────────────────────┘     │             │
│                  └────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                            │ payload (validated + sanitized)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ L3: EntityCard / PropertiesPreview / PropertyEditor             │
│   Recibe props, emite onChange. No sabe del grafo.             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componentes clave: responsabilidades detalladas

### GraphEditorPage.tsx (L1)

```typescript
export function GraphEditorPage() {
  const { data: rawData, isLoading } = useQuery({
    queryKey: ['graph'],
    queryFn: () => mockClient.getGraph(),
  });

  const saveMutation = useMutation({
    mutationFn: (ast: { nodes: ASTNode[]; edges: ASTEdge[] }) =>
      mockClient.saveGraph(graphToDomain(ast.nodes, ast.edges)),
  });

  if (isLoading) return <LoadingSkeleton />;

  const { nodes, edges } = schemaToGraph(rawData, schema);

  return (
    <GraphEditor
      initialNodes={nodes}
      initialEdges={edges}
      onSave={(n, e) => saveMutation.mutate({ nodes: n, edges: e })}
    />
  );
}
```

~30 líneas. Fetch, traduce, renderiza. Nada más.

### GraphCanvas.tsx (L2 — el wrapper de ReactFlow)

```typescript
export function GraphCanvas() {
  const nodes = useGraphStore(s => s.nodes);
  const edges = useGraphStore(s => s.edges);
  const { fitView } = useReactFlow();

  const nodeTypes = useMemo(() => ({
    node: NodeShell,
    group: GroupShell,
  }), []);

  const edgeTypes = useMemo(() => ({
    floating: FloatingEdge,
    button: ButtonEdge,
  }), []);

  const isValidConnection = useConnectionValidation();

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      isValidConnection={isValidConnection}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView
    >
      <Background />
      <Controls />
      <MiniMap />
      <Panel position="top-right">
        <ViewControls />
      </Panel>
    </ReactFlow>
  );
}
```

Solo ReactFlow + configuración. La lógica de negocio vive en los hooks y el store.

### NodeShell.tsx (L2 — render tiers)

```typescript
const ZOOM_DETAIL = 0.9;
const ZOOM_LABEL = 0.4;

const zoomSelector = (s: ReactFlowState) => {
  const zoom = s.transform[2];
  if (zoom >= ZOOM_DETAIL) return 'detail' as const;
  if (zoom >= ZOOM_LABEL) return 'label' as const;
  return 'dot' as const;
};

export const NodeShell = memo(function NodeShell({ data }: NodeProps) {
  const zoomLevel = useStore(zoomSelector);
  const { typeId, payload, visualToken } = data;

  return (
    <BaseNode>
      <Handle type="target" position={Position.Top} />
      <BaseNodeHeader>
        <BaseNodeHeaderTitle>{payload.title}</BaseNodeHeaderTitle>
      </BaseNodeHeader>
      <BaseNodeContent>
        <InternalNodeRouter
          typeId={typeId}
          payload={payload}
          zoomLevel={zoomLevel}
        />
      </BaseNodeContent>
      <Handle type="source" position={Position.Bottom} />
    </BaseNode>
  );
});
```

### use-edge-inheritance.ts (collapse/expand)

```typescript
export function useEdgeInheritance() {
  const { nodes, edges, updateNode, updateEdge } = useGraphStore();

  const collapseGroup = useCallback((groupId: string) => {
    const childIds = nodes
      .filter(n => n.parentId === groupId)
      .map(n => n.id);

    // 1. Ocultar hijos
    childIds.forEach(id => updateNode(id, { hidden: true }));

    // 2. Reasignar edges externas al padre
    edges.forEach(e => {
      const sourceIsChild = childIds.includes(e.source);
      const targetIsChild = childIds.includes(e.target);

      if (sourceIsChild && targetIsChild) {
        // Edge interna: ocultar
        updateEdge(e.id, { hidden: true });
      } else if (sourceIsChild || targetIsChild) {
        // Edge externa: heredar al padre
        updateEdge(e.id, {
          source: sourceIsChild ? groupId : e.source,
          target: targetIsChild ? groupId : e.target,
          className: 'inherited',
          data: {
            ...e.data,
            _originalSource: e.source,
            _originalTarget: e.target,
          },
        });
      }
    });
  }, [nodes, edges]);

  const expandGroup = useCallback((groupId: string) => {
    // Restaurar hijos
    nodes
      .filter(n => n.parentId === groupId)
      .forEach(n => updateNode(n.id, { hidden: false }));

    // Restaurar edges originales
    edges
      .filter(e => e.data?._originalSource || e.data?._originalTarget)
      .forEach(e => {
        updateEdge(e.id, {
          source: e.data._originalSource ?? e.source,
          target: e.data._originalTarget ?? e.target,
          className: '',
          hidden: false,
          data: {
            ...e.data,
            _originalSource: undefined,
            _originalTarget: undefined,
          },
        });
      });
  }, [nodes, edges]);

  return { collapseGroup, expandGroup };
}
```

---

## Pipeline de traducción: schemaToGraph

```typescript
// lib/schema-to-graph.ts

/** Fase 1: Matchear datos crudos contra reglas del schema */
function matchNodes(rawData: unknown, nodeTypes: NodeTypeRule[]): MatchedNode[];

/** Fase 2: Resolver topología (parent/child, groups) */
function resolveTopology(matched: MatchedNode[], topologyRules: TopologyRule[]): TopologyGraph;

/** Fase 3: Resolver edges */
function resolveEdges(topology: TopologyGraph, edgeTypes: EdgeTypeRule[]): RawAST;

/** Fase 4: Validar payloads contra Zod schemas del registry */
function validateAST(ast: RawAST, registry: NodeTypeRegistry): {
  nodes: ASTNode[];       // válidos
  edges: ASTEdge[];       // válidos
  errors: ValidationError[];  // nodos que fallan → se renderizan como ErrorNode
};

/** Pipeline completo */
export function schemaToGraph(rawData: unknown, schema: Schema): ValidatedAST {
  const matched = matchNodes(rawData, schema.nodeTypes);
  const topology = resolveTopology(matched, schema.topology);
  const rawAst = resolveEdges(topology, schema.edgeTypes);
  return validateAST(rawAst, registry);
}
```

Cada fase es testeable independientemente. Los errores de validación producen nodos `ErrorNode`, no crashes.

---

## CSS: Patrón xy-theme

```css
/* L2-canvas/xy-theme.css */

.react-flow {
  /* Tokens de tema */
  --xy-theme-selected: #F57DBD;
  --xy-theme-hover: #C5C5C5;
  --xy-theme-edge-hover: black;

  /* Variables RF */
  --xy-node-border-default: 1px solid #EDEDED;
  --xy-node-border-radius-default: 8px;
  --xy-node-boxshadow-default:
    0px 3.54px 4.55px 0px #00000005,
    0px 3.54px 4.55px 0px #0000000D;

  --xy-handle-background-color-default: #ffffff;
  --xy-handle-border-color-default: #AAAAAA;
}

/* Dark mode */
.react-flow.dark {
  --xy-node-boxshadow-default:
    0px 3.54px 4.55px 0px rgba(255, 255, 255, 0.05),
    0px 3.54px 4.55px 0px rgba(255, 255, 255, 0.13);
}

/* Node tokens por tipo (viene del registry.colorToken) */
.react-flow__node[data-type="person"] { --node-color: #8B5CF6; }
.react-flow__node[data-type="skill"]  { --node-color: #06B6D4; }
.react-flow__node[data-type="project"]{ --node-color: #F59E0B; }

/* Estado de nodo */
.react-flow__node {
  border-color: var(--node-color, var(--xy-node-border-default));
}
.react-flow__node.selectable.selected {
  border-color: var(--xy-theme-selected);
}

/* Edges heredadas (collapse) */
.react-flow__edge.inherited .react-flow__edge-path {
  stroke-dasharray: 5, 5;
  opacity: 0.6;
}

/* Touch support */
@media (pointer: coarse) {
  .react-flow__handle {
    width: 20px;
    height: 20px;
  }
}
```

---

## Focus Management (contrato de foco)

Dos modos, inspirado en Google Sheets:

| Modo | Owner del foco | Teclado | Transición |
|------|---------------|---------|------------|
| **Canvas** | L2 | Flechas navegan entre nodos. Tab cicla. Delete borra. | `Enter` → modo Edit |
| **Edit** | L3 | El componente L3 captura todo el input. | `Escape` → modo Canvas |

```typescript
// hooks/use-keyboard.ts
function useKeyboard() {
  const editorState = useUIStore(s => s.editorState);

  // Canvas mode: L2 shortcuts
  useKeyPress('Delete', () => {
    if (editorState === 'browse') deleteSelection();
  });

  useKeyPress('Enter', () => {
    if (editorState === 'browse') setEditorState('edit_node');
  });

  useKeyPress('Escape', () => {
    if (editorState === 'edit_node') setEditorState('browse');
  });

  // Ctrl+Z: depende del modo
  useKeyPress(['Meta+z', 'Ctrl+z'], () => {
    if (editorState === 'browse') graphStore.undo();
    // En edit mode, el componente L3 maneja su propio undo
  });
}
```

---

## Dependencias a agregar

```json
{
  "nuevas": {
    "elkjs": "layout de compound nodes",
    "zustand": "state management",
    "zod": "validación runtime de payloads",
    "dompurify": "sanitización de contenido HTML",
    "@radix-ui/react-*": "via shadcn/ui (Sheet, Accordion, AlertDialog, ContextMenu)"
  },
  "existentes que se mantienen": {
    "@xyflow/react": "^12.10.1",
    "@tanstack/react-query": "^5.94.5",
    "tailwindcss": "^3.4.17",
    "lucide-react": "^0.577.0"
  },
  "a eliminar": {
    "dagre": "reemplazado por elkjs",
    "@dagrejs/dagre": "reemplazado por elkjs"
  }
}
```

---

## Mapeo de migración: KnowledgeGraph.tsx → target

| Sección actual (líneas) | Target | Archivo |
|-------------------------|--------|---------|
| Types + constants (35-200) | Types compartidos + schema JSON | `types.ts` + `node-types.schema.json` |
| `CATEGORY_COLORS` (80-130) | Registry color tokens | `xy-theme.css` + `register-defaults.ts` |
| `NODE_TEMPLATES` (130-180) | Registry definitions | `register-defaults.ts` |
| `KnowledgeGraphContext` (180-200) | Zustand stores | `graph-store.ts` + `ui-store.ts` |
| Utility functions (201-280) | Helpers del store | `graph-store.ts` internals |
| `SidebarSection` (280-320) | shadcn Accordion | `CanvasSidebar.tsx` |
| Property editor helpers (439-550) | Componente L3 | `components/content/PropertyEditor.tsx` |
| `SimpleNodeCard` (551-650) | BaseNode + EntityCard | `NodeShell.tsx` + `EntityCard.tsx` |
| `GroupNode` (650-698) | LabeledGroupNode | `GroupShell.tsx` |
| `FloatingEdge` (734-770) | Ejemplo oficial RF | `edges/FloatingEdge.tsx` |
| `SubFlowEdge` (770-799) | Eliminado (FloatingEdge con style) | — |
| Layout dagre (801-880) | elkjs hook | `hooks/use-graph-layout.ts` |
| Persistence (881-912) | Graph store | `graph-store.ts` |
| ~40 useState (923-980) | Zustand stores | `graph-store.ts` + `ui-store.ts` |
| Sidebar UI (1800-2600) | Sidebar sections | `sidebar/*.tsx` |
| Node editor modal (2600-2800) | Sheet inspector | `panels/NodeInspector.tsx` |
| Edge editor modal (2800-2900) | Sheet inspector | `panels/EdgeInspector.tsx` |
| Delete confirmation (2900-2939) | shadcn AlertDialog | Inline en `ActionsSection.tsx` |
| Keyboard handler useEffect | RF useKeyPress | `hooks/use-keyboard.ts` |
| Camera auto-pan useEffect | RF `autoPanOnConnect` prop | Eliminado |

---

## Docs relacionados

- `ARCHITECTURE.md` — Modelo de 3 capas (actualizar con definiciones corregidas)
- `_meta/architecture_critique.md` — Problemas y recomendaciones (14 puntos)
- `_meta/reactflow_patterns_catalog.md` — 20 patrones RF con código copiable
- `_meta/reactflow_inventory.md` — Inventario RF nativo vs custom
- `_meta/session_reactflow_deep_dive.md` — Hallazgos y decisiones de esta sesión
