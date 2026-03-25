# Sesión: ReactFlow Deep Dive + Auditoría de src/

> Decisiones, hallazgos y correcciones derivadas de la revisión exhaustiva de ejemplos ReactFlow y la exploración del código actual.

---

## Ejemplos revisados

```
https://reactflow.dev/examples/nodes/stress
https://reactflow.dev/examples/nodes/intersections
https://reactflow.dev/examples/nodes/node-toolbar
https://reactflow.dev/examples/edges/custom-edges
https://reactflow.dev/examples/interaction/touch-device
https://reactflow.dev/examples/interaction/save-and-restore
https://reactflow.dev/examples/interaction/drag-and-drop
https://reactflow.dev/examples/grouping/parent-child-relation
https://reactflow.dev/examples/layout/elkjs
https://reactflow.dev/examples/grouping/sub-flows
https://reactflow.dev/examples/layout/node-collisions
https://reactflow.dev/examples/whiteboard/rectangle
https://reactflow.dev/examples/interaction/context-menu
https://reactflow.dev/examples/interaction/contextual-zoom
https://reactflow.dev/examples/interaction/validation
https://reactflow.dev/examples/edges/floating-edges
https://reactflow.dev/examples/nodes/update-node
https://reactflow.dev/ui/components/database-schema-node
https://reactflow.dev/ui/components/node-appendix
https://reactflow.dev/ui/components/node-tooltip
https://reactflow.dev/ui/components/devtools
```

Cada ejemplo fue descargado, su código fuente analizado, y los patrones útiles extraídos en `_meta/reactflow_patterns_catalog.md`.

---

## Hallazgo: El patrón CSS de los ejemplos oficiales

Todos los ejemplos de ReactFlow siguen una separación de 2 archivos CSS:

- **`xy-theme.css`** — Overrides de variables `--xy-*` y clases `.react-flow__*`. Tema visual puro: colores, sombras, estados hover/selected/focus, dark mode. El archivo tiene un comment: `/* xyflow theme files. Delete these to start from our base */`.
- **`index.css`** — `@import url('./xy-theme.css')` + boilerplate + estilos custom del ejemplo.
- **`App.jsx`** — `import '@xyflow/react/dist/style.css'` (base de RF).

ReactFlow ofrece dos niveles de CSS base:

| Import | Qué incluye | Cuándo usar |
|--------|-------------|-------------|
| `@xyflow/react/dist/style.css` | Base + tema default | Partir de los defaults y overridear |
| `@xyflow/react/dist/base.css` | Solo lo mínimo funcional | Tema 100% custom (ej. Tailwind puro) |

**Decisión:** Adoptar este patrón. Crear nuestro `xy-theme.css` con tokens MD3/Obsidian-style. Separar tema visual de lógica de componentes.

---

## Hallazgo: Contextual Zoom = Render Tiers

El ejemplo `contextual-zoom` resuelve el problema de performance documentado en la critique arquitectónica. Usa `useStore` con un selector atómico para decidir qué renderizar según el nivel de zoom:

```typescript
const zoomSelector = (s) => s.transform[2] >= 0.9;
const showContent = useStore(zoomSelector);
```

**Decisión:** Adoptar como mecanismo de render tiers en NodeShell (L2). Tres niveles:
- `zoom >= 0.9` → L3 completo (editor, markdown, JSON)
- `zoom >= 0.4` → Solo título + icono de tipo
- `zoom < 0.4` → Punto de color

Con esto, 1000 nodos es viable — solo ~10 renderizan contenido L3 pesado.

---

## Hallazgo: DnD oficial usa Pointer Events

El ejemplo `drag-and-drop` usa pointer events nativos (no HTML Drag API). Funciona en touch y desktop con el mismo código. Nuestra implementación actual usa `onTemplateDragStart` (HTML drag API).

**Decisión:** Migrar al patrón de pointer events de RF. Más robusto y unifica touch/desktop.

---

## Hallazgo: `getIntersectingNodes` — API nativa no usada

`useReactFlow().getIntersectingNodes(node)` detecta qué nodos se solapan con un nodo arrastrado. Es la base para "drag to reparent" (arrastrar un nodo sobre un grupo para hacerlo hijo).

**Decisión:** Adoptar para la funcionalidad de reparenting en subflows.

---

## Hallazgo: Connection Validation con feedback visual gratis

RF ya tiene clases CSS `.react-flow__handle.valid` (verde) y `.connectingto` (rojo) que se aplican automáticamente durante el drag de conexión. Solo necesitas pasar `isValidConnection` al componente.

**Decisión:** Implementar validación desde el schema/registry:

```typescript
const isValidConnection = (connection) => {
  const source = getNode(connection.source);
  const target = getNode(connection.target);
  return registry.canConnect(source.data.typeId, target.data.typeId);
};
```

---

## Exploración del src/ — Estado actual del código

### Estructura

```
apps/review-workbench/src/
├── App.tsx                          ← fetch + QueryClient
├── components/layouts/AppShell.tsx   ← shell de navegación
├── pages/global/KnowledgeGraph.tsx   ← 2,949 líneas — TODO vive aquí
├── utils/cn.ts                       ← tailwind merge
├── mock/client.ts                    ← mock API (80ms delay)
└── mock/fixtures/graph_data.json     ← datos de ejemplo
```

### Lo que vive dentro del God Component (KnowledgeGraph.tsx)

| Sección | Líneas | Contenido |
|---------|--------|-----------|
| Types + constants | 35-200 | `SimpleNodeData`, `EditorState`, `CATEGORY_COLORS` (20+ categorías), `NODE_TEMPLATES` (8 templates), `KnowledgeGraphContext` |
| Utilities | 201-280 | `createEntityId`, `upsertItemsById`, clipboard helpers |
| Property editor | 439-550 | `PropertyValueInput` — input multi-tipo (string, markdown, date, enum, boolean) |
| SimpleNodeCard | 551-650 | Nodo custom: bordes por categoría, 4 handles, botones Focus/Edit, propiedades colapsables |
| GroupNode | 650-698 | Contenedor colapsable con conteo de hijos |
| FloatingEdge | 734-770 | Edge con routing Bezier inteligente (intersección rect-rect) |
| SubFlowEdge | 770-799 | Copia de FloatingEdge con stroke cyan `#00f2ff` |
| Layout (dagre) | 801-880 | `layoutAllDeterministic()` (LR, 52px nodesep, 120px ranksep), `layoutFocusNeighborhood()` |
| Persistence | 881-912 | Serialización JSON para dirty detection, snapshots de posiciones |
| NodeEditorInner | 923-2939 | Componente principal: ~40 useState, ~30 callbacks, sidebar, modals, canvas |

### Estado — ~40 variables en useState (no hay store)

- **Graph:** `nodes`, `edges` (RF hooks)
- **UI:** `editorState` (browse/focus/focus_relation/edit_node/edit_relation), `focusedNodeId`, `sidebarOpen`, secciones
- **Editing:** `nodeDraft`, `edgeDraft`, `connectMenu`, `copiedNode`
- **History:** `undoStack[]`, `redoStack[]` — 4 action types: `create_elements`, `delete_elements`, `update_node`, `update_edge`
- **Filters:** `hiddenRelationTypes`, `filterText`, `attributeFilterKey/Value`, `hideNonNeighbors`

### Lo que NO existe

- No Zustand / no store externo — todo useState local
- No shadcn/ui — divs con tailwind manual
- No schemas `.schema.json` — tipos de nodo hardcoded en `CATEGORY_COLORS` y `NODE_TEMPLATES`
- No router — una sola página
- No elkjs — solo dagre
- No `schemaToGraph()` — no hay AST intermedio
- No `BaseNode` / `UniversalGraphCanvas` — solo el componente monolítico

### Dependencias actuales

```json
{
  "@xyflow/react": "^12.10.1",
  "@tanstack/react-query": "^5.94.5",
  "dagre": "^0.8.5",
  "@dagrejs/dagre": "^1.1.5",
  "tailwindcss": "^3.4.17",
  "lucide-react": "^0.577.0"
}
```

---

## Corrección: FloatingEdge y SubFlowEdge NO deben mantenerse custom

Al comparar nuestro código con el ejemplo oficial `reactflow.dev/examples/edges/floating-edges`:

| Nuestro código | Ejemplo oficial RF |
|---------------|-------------------|
| `getNodeIntersection()` custom | `getNodeIntersection()` — mismo algoritmo |
| Calcula posiciones manualmente | Usa `node.internals.positionAbsolute` (API actual) |
| SubFlowEdge = copia con color cyan | No existe — es un color, no un tipo |

**Decisión:**

| Edge | Acción |
|------|--------|
| FloatingEdge | **Reemplazar** con el ejemplo oficial de RF (usa APIs actuales) |
| SubFlowEdge | **Eliminar** — un solo FloatingEdge con `style={{ stroke }}` configurable desde el `visualToken` |
| ButtonEdge | **Adoptar** — nuevo, patrón del catálogo con `EdgeLabelRenderer` + botón [×] |
| ProxyEdge | **Rediseñar** → Edge Inheritance (ver sección siguiente) |

---

## Rediseño: ProxyEdge → Edge Inheritance

### El problema original

Cuando un grupo se colapsa, sus nodos hijos se ocultan. Pero esos hijos pueden tener edges conectadas a nodos externos. ¿Qué pasa con esas edges?

### El concepto anterior: ProxyEdge

Crear edges temporales nuevas que conectan el grupo padre con los nodos externos. Destruirlas al expandir.

**Problemas:**
- Estado distribuido (crear/destruir edges al toggle)
- Complejidad en undo (deshacer collapse = recrear edges originales)
- Nuevo tipo de edge custom sin equivalente en RF

### El concepto nuevo: Edge Inheritance

Las edges de los hijos no se destruyen ni se crean nuevas. Al colapsar un grupo:

1. Los nodos hijos se ocultan (`hidden: true`)
2. Las edges que conectan hijos con nodos externos se **reasignan visualmente** al padre (el source o target apunta al grupo en vez del hijo)
3. Esas edges heredadas se renderizan con un **estilo visualmente distinto** (punteado, menor opacidad, label "via N hijos")
4. Al expandir, las edges vuelven a apuntar a sus nodos originales

```
EXPANDIDO:                          COLAPSADO:

┌─ Terrestres ──────┐              ┌─ Terrestres ─┐
│  ┌─────┐          │              │  (3 hijos)   │
│  │Auto │──────────┼──→ Ruedas    │              ├ ─ ─ → Ruedas
│  └─────┘          │              │              │
│  ┌──────┐         │              │              ├ ─ ─ → Orugas
│  │Tanque│─────────┼──→ Orugas    │              │
│  └──────┘         │              └──────────────┘
│  ┌──────┐         │
│  │Moto  │─────────┼──→ Ruedas    Edges heredadas: punteadas,
│  └──────┘         │              opacidad reducida, o con
└───────────────────┘              indicador "via hijo"
```

### Por qué es mejor

| ProxyEdge | Edge Inheritance |
|-----------|-----------------|
| Crea edges temporales al colapsar | Las edges originales se redirigen |
| Estado distribuido complejo | Sin estado extra — solo cambia quién renderiza |
| Custom edge type nuevo | Mismo FloatingEdge con clase CSS `.inherited` |
| Undo complejo (recrear edges) | Sin complejidad en undo — edges originales intactas en el AST |

### Estilo visual

No necesita un edge type custom. Solo una clase CSS o un `visualToken` diferente:

```css
/* En xy-theme.css */
.react-flow__edge.inherited .react-flow__edge-path {
  stroke-dasharray: 5, 5;
  opacity: 0.6;
}
```

La distinción semántica: "todos los autos tienen ruedas, pero no todos los vehículos terrestres — también hay tanques con orugas". La edge punteada comunica exactamente eso: "esta conexión existe **a través de** un hijo, no es propiedad directa del padre".

### Lógica de collapse

```typescript
function collapseGroup(groupId: string, nodes: Node[], edges: Edge[]) {
  const childIds = nodes
    .filter(n => n.parentId === groupId)
    .map(n => n.id);

  // 1. Ocultar hijos
  const updatedNodes = nodes.map(n =>
    childIds.includes(n.id) ? { ...n, hidden: true } : n
  );

  // 2. Reasignar edges externas al padre
  const updatedEdges = edges.map(e => {
    const sourceIsChild = childIds.includes(e.source);
    const targetIsChild = childIds.includes(e.target);
    const isExternal = sourceIsChild !== targetIsChild; // una punta adentro, otra afuera

    if (!isExternal) {
      // Edge interna (hijo→hijo): ocultar
      return (sourceIsChild && targetIsChild)
        ? { ...e, hidden: true }
        : e;
    }

    // Edge externa: reasignar la punta interna al grupo padre
    return {
      ...e,
      source: sourceIsChild ? groupId : e.source,
      target: targetIsChild ? groupId : e.target,
      className: 'inherited',
      data: {
        ...e.data,
        _originalSource: e.source,  // guardar para restore
        _originalTarget: e.target,
      },
    };
  });

  return { nodes: updatedNodes, edges: updatedEdges };
}
```

---

## Mapeo: Código actual → Target L1/L2/L3

| Pieza actual (KnowledgeGraph.tsx) | Target | Capa |
|----------------------------------|--------|------|
| `App.tsx` + fetch | Se mantiene, crece con router | L1 |
| `AppShell.tsx` | Se mantiene | L1 |
| Sidebar completa | → componente propio con `Accordion` de shadcn | L1 |
| Node/Edge editor modals | → `Sheet` (panel lateral) de shadcn | L1 |
| Filtros | → modifican AST antes de pasarlo al canvas | L1 |
| `CATEGORY_COLORS` + `NODE_TEMPLATES` | → schema `.json` + node type registry | L1 |
| ReactFlow + layout | → `UniversalGraphCanvas` con elkjs | L2 |
| `SimpleNodeCard` + `GroupNode` | → `BaseNode` + `LabeledGroupNode` de RF UI | L2 |
| `FloatingEdge` | → ejemplo oficial de RF (no custom) | L2 |
| `SubFlowEdge` | → eliminar, FloatingEdge con visualToken | L2 |
| `PropertyValueInput` | → componente L3 standalone | L3 |
| History (`undoStack/redoStack`) | → Zustand store con acciones semánticas serializables | Transversal |
| `KnowledgeGraphContext` | → Zustand con selectores atómicos | Transversal |
| ~40 useState | → distribuir entre Zustand (state) y componentes (UI local) | Transversal |

---

## Documentos generados en esta sesión

1. **`_meta/reactflow_patterns_catalog.md`** — 20 patrones con código copiable, priorizados por fase de adopción
2. **`_meta/reactflow_inventory.md`** — Inventario RF nativo vs custom + decisiones de stack (actualizado con elkjs como decisión firme)
3. **`_meta/session_reactflow_deep_dive.md`** — Este documento

## Documentos actualizados en esta sesión

4. **`_meta/architecture_critique.md`** — Punto 4 (dagre vs elkjs) marcado como RESUELTO
