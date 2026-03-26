# Node Editor Architecture

> **Modelo de 3 Capas** — Arquitectura definitiva para el editor de grafos.

---

## Las 3 Capas

| Capa | Nombre | Pregunta que responde | Ejemplo |
|------|--------|----------------------|---------|
| **L1** | **App** (Router + Data) | "¿Qué documento estoy viendo?" | `GraphEditorPage`, `App.tsx`, `AppShell` |
| **L2** | **Canvas** (Editor completo) | "¿Todo lo que hago dentro de un documento?" | `GraphCanvas`, `CanvasSidebar`, `NodeShell`, inspectors |
| **L3** | **Content** (Componentes reutilizables) | "¿Cómo muestro/edito este dato?" | `EntityCard`, `PropertyEditor`, `PropertiesPreview` |

**Regla de Oro:** Un nivel no puede saltarse a otro ni conocer la lógica del otro.

**Test de frontera:** Si sacas L2 y lo pones en otra página, se lleva sus propios controles (sidebar, inspectors, undo, filtros). Si pones un componente L3 fuera de un nodo (en un Sheet, una tabla, un modal), funciona igual.

### Data Down, Events Up

```
L1 ──(AST nodes/edges)──→ L2 ──(payload vía registry)──→ L3
L1 ←──(onSave)────────── L2 ←──(onChange callbacks)────── L3
```

- **Data Down:** L1 traduce datos crudos a AST y se los pasa a L2 via props. L2 extrae el payload por typeId (via Node Type Registry) y se lo pasa a L3.
- **Events Up:** L3 emite `onChange` (callback recibido como prop). L2 atrapa el evento, actualiza el store Zustand. L1 solo se entera cuando L2 dispara `onSave`.

---

## L1 — App (Router + Data Loader)

> Delgado. Decide qué abrir, carga los datos, traduce schema→AST, y monta el editor correspondiente.

### Responsabilidades

- Routing entre páginas (`App.tsx`)
- Layout global: nav, breadcrumbs (`AppShell.tsx`)
- Fetch de datos (API / mock) → `useQuery`
- Traducción dominio→AST (`schemaToGraph()`)
- Montar el editor con props tipados

### Lo que L1 NO contiene

Sidebar, filtros, undo, save, inspectors, creation palette. Todo eso es del editor (L2).

### Docs

- `L1_ui_app/schema_translation.md` — Motor de traducción Schema→AST
- `L1_ui_app/schema_integration.md` — Integración con APIs
- `L1_ui_app/document_explorer.md` — Explorador
- `L1_ui_app/validation_testing.md` — Testing

---

## L2 — Canvas (El Editor Completo)

> Self-contained. Si lo sacas y lo pones en otra página, lleva sus propios controles consigo.

### Responsabilidades

| Área | Archivos |
|------|----------|
| Canvas ReactFlow | `GraphCanvas.tsx` |
| Nodos: cascarón + render tiers | `NodeShell.tsx`, `GroupShell.tsx` |
| Router de contenido L3 | `InternalNodeRouter.tsx` |
| Edges | `edges/FloatingEdge.tsx`, `edges/ButtonEdge.tsx` |
| Sidebar del editor | `sidebar/CanvasSidebar.tsx`, `sidebar/ActionsSection.tsx`, `sidebar/FiltersSection.tsx`, `sidebar/CreationSection.tsx`, `sidebar/ViewSection.tsx` |
| Inspectors (Sheet lateral) | `panels/NodeInspector.tsx`, `panels/EdgeInspector.tsx` |
| Layout (elkjs) | `hooks/use-graph-layout.ts` |
| Collapse/expand grupos | `hooks/use-edge-inheritance.ts` |
| DnD sidebar→canvas | `hooks/use-dnd.ts` |
| Keyboard shortcuts | `hooks/use-keyboard.ts` |
| Validación de conexiones | `hooks/use-connection-validation.ts` |
| Tema visual | `xy-theme.css` |

### Motor de layout

**elkjs** (no dagre). Soporta compound layouts (nodos dentro de nodos) que son requisito para subflows anidados.

### Render tiers (performance)

Basado en `useStore(s => s.transform[2])` del ejemplo oficial `contextual-zoom`:

| Zoom | Tier | Contenido |
|------|------|-----------|
| `>= 0.9` | detail | L3 completo (editores, markdown, JSON) |
| `0.4–0.9` | label | Solo título + icono de tipo |
| `< 0.4` | dot | Punto de color |

### Edge Inheritance (collapse de grupos)

Al colapsar un grupo, los edges de hijos ocultos se reasignan visualmente al padre (no se crean/destruyen edges). Estilo visual: `stroke-dasharray: 5,5; opacity: 0.6` vía clase CSS `.inherited`.

### Docs

- `L2_graph_viewer/graph_foundations.md`
- `L2_graph_viewer/layout_presets.md`
- `L2_graph_viewer/node_types.md`
- `L2_graph_viewer/state_history.md`
- `L2_graph_viewer/subflows.md`
- `L2_graph_viewer/tree_mode.md`

---

## L3 — Content (Componentes Reutilizables)

> Agnósticos al grafo. Funcionan en un nodo, en un Sheet lateral, en una tabla, o en un modal.

### Responsabilidades

- Mostrar datos enriquecidos o interactivos
- Manejar estados de edición locales
- Emitir cambios vía callbacks (props)

### Lo que L3 NO importa

Stores, hooks del canvas, ReactFlow, nada de L2. Son componentes React puros con `props` y `onChange`.

Viven en `components/content/` porque son reutilizables entre features (no dentro de `features/graph-editor/`).

### Docs

- `L3_internal_nodes/rich_content_nodes.md`
- `L3_internal_nodes/markdown_editor.md`
- `L3_internal_nodes/json_yaml_views.md`
- `L3_internal_nodes/table_editor.md`
- `L3_internal_nodes/code_annotation.md`
- `L3_internal_nodes/image_annotation.md`

---

## Contratos entre Capas

### Contrato L1 → L2 (App → Editor)

```typescript
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

### Contrato L2 → L3 (Editor → Contenido)

No hay interfaz formal. El **Node Type Registry** media:

1. `InternalNodeRouter` recibe `typeId` + `payload`
2. Consulta el registry → obtiene `payloadSchema` (Zod) + `sanitizer` + `renderer`
3. Valida el payload en runtime con Zod
4. Sanitiza con DOMPurify (default deny)
5. Renderiza el componente L3 dentro de `<Suspense>`

```typescript
interface NodeTypeDefinition {
  typeId: string;
  payloadSchema: ZodSchema;          // validación runtime
  sanitizer?: (payload: unknown) => unknown;
  renderers: {
    dot: ComponentType;               // zoom < 0.4
    label: ComponentType;             // zoom 0.4-0.9
    detail: ComponentType | LazyExoticComponent;  // zoom >= 0.9
  };
  allowedConnections: string[];       // typeIds válidos como target
  // ... label, icon, category, colorToken, defaultSize
}
```

### Contrato L3 → L2 (Contenido → Editor)

Callbacks simples recibidos como props:

```typescript
<PropertyEditor
  pairs={node.properties}
  onChange={(newPairs) => {
    graphStore.updateNode(nodeId, { properties: newPairs });
  }}
/>
```

L3 no importa stores ni hooks del canvas. Solo recibe `onChange` como prop.

---

## Estado (Zustand)

Dos stores separados con selectores atómicos (no React Context):

| Store | Contenido | Se persiste | Se deshace |
|-------|-----------|-------------|------------|
| `graph-store` | nodes, edges, history semántico, dirty state | Sí | Sí |
| `ui-store` | editorState, focusedId, sidebar, filters, clipboard | No | No |

**Reglas:**
- Selectores atómicos: `useGraphStore(s => s.nodes)` → solo re-renderiza cuando `nodes` cambia
- Acciones semánticas: objetos serializables `{ type, payload, timestamp, affectedIds }` (no closures)
- Pan/zoom no entran en el historial de undo

---

## Estructura de Archivos

```
plan/
├── README.md
├── GUIDE.md
├── ARCHITECTURE.md                    # Este archivo
│
├── 01_L1_ui_app/                     # Orquestación
│   ├── schema_translation.md
│   ├── schema_integration.md
│   ├── document_explorer.md
│   └── validation_testing.md
│
├── 02_L2_graph_viewer/               # Editor completo
│   ├── graph_foundations.md
│   ├── layout_presets.md
│   ├── node_types.md
│   ├── state_history.md
│   ├── subflows.md
│   └── tree_mode.md
│
├── 03_L3_internal_nodes/             # Contenido reutilizable
│   ├── rich_content_nodes.md
│   ├── markdown_editor.md
│   ├── json_yaml_views.md
│   ├── table_editor.md
│   ├── code_annotation.md
│   └── image_annotation.md
│
├── _meta/                            # Arquitectura + análisis
│   ├── blueprint_node_editor.md      # Blueprint de implementación (THE definitive doc)
│   ├── architecture_critique.md      # Problemas y recomendaciones
│   ├── reactflow_patterns_catalog.md # 20 patrones RF con código copiable
│   ├── reactflow_inventory.md        # RF nativo vs custom + stack decisions
│   ├── session_reactflow_deep_dive.md # Decisiones de la sesión RF
│   ├── flow_contract.md
│   ├── ui_graph_architecture_layers.md
│   └── AGENT_REVIEWER_ENTRYPOINT.md
│
└── _legacy/                          # Referencia
    ├── 00_status_matrix.md
    └── 2026-03-20-ui-plan-review-design.md
```

---

## Stack tecnológico

| Qué | Herramienta | Nota |
|-----|-------------|------|
| Canvas | ReactFlow (`@xyflow/react`) | Core de renderizado, interacción, viewport |
| Layout | elkjs | Compound layouts para subflows anidados |
| State | Zustand | Selectores atómicos, acciones semánticas |
| Validación runtime | Zod | Payloads en Node Type Registry |
| Sanitización | DOMPurify | Default deny en registry |
| UI overlays | shadcn/ui | Sheet, Accordion, AlertDialog, ContextMenu |
| Iconos | lucide-react | Ya presente |
| Styling | Tailwind + xy-theme.css | CSS variables `--xy-*` para tema RF |

---

## Orden de Implementación

1. **L2 (Canvas)** — El núcleo: GraphCanvas + NodeShell + stores + registry
2. **L3 (Content)** — Una vez L2 renderiza cascarones estables
3. **L1 (App)** — Integración: routing, schemaToGraph, persistencia

---

## Referencias

- `_meta/blueprint_node_editor.md` — Blueprint completo de implementación
- `_meta/architecture_critique.md` — Problemas identificados y recomendaciones
- `_meta/reactflow_patterns_catalog.md` — Patrones RF priorizados con código
- `_meta/reactflow_inventory.md` — Inventario RF nativo vs custom
- `_meta/06_flow_contract.md` — Contratos detallados (legacy, reference only)
- `_meta/06_ui_graph_architecture_layers.md` — Capas visuales (legacy)
