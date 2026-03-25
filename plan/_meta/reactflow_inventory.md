# Inventario ReactFlow: Qué delegar, qué mantener custom

> Mapeo del estado actual de KnowledgeGraph.tsx contra lo que ReactFlow ofrece nativo, y decisiones de stack para la refactorización.

---

## Decisión: elkjs desde el día 1

**Estado:** DECIDIDO — elkjs, no dagre.

Subflows anidados son un requisito inmediato, no futuro. dagre no soporta compound layouts (nodos dentro de nodos). elkjs sí, de forma nativa.

El contrato en `ARCHITECTURE.md` (`layoutEngine: 'dagre' | 'manual'`) debe actualizarse a `layoutEngine: 'elk' | 'manual'`.

Referencia: el ejemplo oficial de ReactFlow para subflows (`reactflow.dev/examples/grouping/sub-flows`) usa posiciones manuales. Para layout automático de subflows, elkjs es la única opción viable.

---

## Patrón CSS de ReactFlow: xy-theme + index

Todos los ejemplos oficiales de ReactFlow siguen una separación de 2 archivos CSS:

### `xy-theme.css` — El tema visual

Overrides de las CSS variables de ReactFlow (`--xy-*`) y estilos de clases internas (`.react-flow__node`, `.react-flow__edge`, `.react-flow__handle`). Controla:

- Colores de nodos (borde, fondo, sombra)
- Estados interactivos (hover, selected, focus)
- Apariencia de handles y edges
- Soporte dark mode (`.react-flow.dark { ... }`)

```css
/* xy-theme.css — ejemplo de la estructura */
.react-flow {
    --xy-theme-selected: #F57DBD;
    --xy-theme-hover: #C5C5C5;
    --xy-node-border-default: 1px solid #EDEDED;
    --xy-node-border-radius-default: 8px;
    --xy-node-boxshadow-default: 0px 3.54px 4.55px 0px #0000000D;
    --xy-handle-background-color-default: #ffffff;
}

.react-flow.dark {
    /* dark mode overrides */
}

.react-flow__node { /* styling */ }
.react-flow__node.selectable:hover { /* hover state */ }
.react-flow__node.selectable.selected { /* selected state */ }
.react-flow__node-group { /* group node styling */ }
.react-flow__edge.selectable:hover .react-flow__edge-path { /* edge hover */ }
.react-flow__handle.connectionindicator:hover { /* handle hover */ }
```

### `index.css` — Boilerplate de la app + import del theme

```css
@import url('./xy-theme.css');

html, body {
  margin: 0;
  font-family: sans-serif;
}

#app {
  width: 100vw;
  height: 100vh;
}

/* Custom styles específicos del ejemplo (context menu, button edges, etc.) */
```

### `App.jsx` — Importa `style.css` de ReactFlow

```jsx
import '@xyflow/react/dist/style.css';  // estilos base de RF
// xy-theme.css se carga vía index.css, NO aquí
```

### Cómo aplicar esto en nuestro proyecto

ReactFlow ofrece dos niveles de CSS:

| Import | Qué incluye | Cuándo usar |
|--------|-------------|-------------|
| `@xyflow/react/dist/style.css` | Base + tema default de RF | Si quieres partir de sus defaults y overridear |
| `@xyflow/react/dist/base.css` | Solo lo mínimo funcional | Si quieres tema 100% custom (ej. con Tailwind) |

**Recomendación para nuestro proyecto:**

1. Importar `style.css` (defaults de RF como punto de partida)
2. Crear nuestro `xy-theme.css` con los overrides de variables `--xy-*` para nuestro tema (tokens MD3, Obsidian-style)
3. `index.css` importa `xy-theme.css` + estilos de app
4. Estilos de componentes custom (FloatingEdge, SubFlowEdge, etc.) viven en sus propios archivos o en `index.css`

Esta separación permite cambiar el tema visual completo sin tocar ningún componente React.

---

## Inventario: Qué usa RF nativo vs custom

### Actualmente usando de ReactFlow

| Feature | Import | Status |
|---------|--------|--------|
| `ReactFlow` | Componente principal | ✅ Usando |
| `useNodesState` | Estado de nodos | ✅ Usando |
| `useEdgesState` | Estado de aristas | ✅ Usando |
| `useReactFlow` | API del canvas (fitView, screenToFlowPosition) | ✅ Usando |
| `Background` | Fondo con grid | ✅ Usando |
| `Controls` | Botones zoom/fit | ✅ Usando |
| `MiniMap` | Minimapa | ✅ Usando |
| `Handle` | Puntos de conexión | ✅ Usando |
| `Position` | TOP/RIGHT/BOTTOM/LEFT | ✅ Usando |
| `BaseEdge` | Renderizar aristas | ✅ Usando |
| `getBezierPath` | Calcular path de aristas | ✅ Usando |
| `ReactFlowProvider` | Contexto | ✅ Usando |
| `NodeToolbar` | Toolbar sobre grupos | ✅ Usando |

### Implementado custom (mantener custom)

| Feature | Razón para mantener custom |
|---------|---------------------------|
| Layout engine (→ elkjs) | RF no tiene layout automático anidado. elkjs es el motor. |
| History/Undo (Zustand) | Debe ser semántico (create/edit/delete), no visual (pan/zoom). El historial de RF mezcla ambos. |
| Selection/filtrado de vecinos | Lógica de negocio (hideNonNeighbors). RF solo da selección espacial. |
| FloatingEdge | Custom edge con cálculo de intersección. RF no tiene floating edges en el core. |
| SubFlowEdge | Custom edge entre grupos. Específico de nuestra topología. |
| ProxyEdge | NO implementado aún. Necesario para collapse de grupos. |

### No usando de RF pero deberíamos

| Feature RF | Reemplaza nuestro... | Beneficio |
|-----------|---------------------|-----------|
| `<Panel position="...">` | `<div className="absolute ... z-50">` para controles overlay | RF maneja z-index y previene click-through al canvas |
| `useOnSelectionChange` | `onNodeClick` manual + `focusedNodeId` state | Reactivo, sin interceptar cada clic |
| `useKeyPress` | `useEffect` con `window.addEventListener("keydown")` | Más limpio, maneja combinaciones (Meta+c, Ctrl+c) |
| `autoPanOnConnect` / `autoPanOnNodeDrag` | `useEffect` custom con `onMouseMove` + `requestAnimationFrame` | Elimina todo el auto-pan custom |
| `deleteKeyCode` + `onNodesDelete` | Manejo manual de Delete key | Delegar a RF el evento, interceptar solo para confirmar |
| `colorMode="dark"` prop | Tema manual | RF aplica `.dark`/`.light` automáticamente |

---

## Decisiones de stack

### L2 (Canvas): ReactFlow + elkjs

- **ReactFlow** para todo lo espacial: renderizado, interacción, viewport, edges, handles
- **elkjs** para layout automático (compound/nested). En Web Worker solo cuando el grafo supere ~200 nodos.
- **Zustand** para estado compartido del editor (history, selection, view state). NO usar el state interno de RF como fuente de verdad.

### L1/L2 overlays: shadcn/ui

| Actual (UI cruda) | Migrar a shadcn |
|-------------------|-----------------|
| Modal de borrado (`fixed inset-0 bg-slate-900/35`) | `AlertDialog` — confirmaciones destructivas con focus trap correcto |
| Menú de conexión flotante (cálculo manual X/Y) | `DropdownMenu` o `Popover` — floating-ui maneja posicionamiento |
| NodeShell (div con bordes) | `Card` (CardHeader, CardContent) — contenedor universal L2 |
| Modales de edición (modal central) | `Sheet` — panel lateral deslizable para editar sin bloquear el canvas |
| SidebarSection (button +/- manual) | `Accordion` — animaciones + teclado gratis |
| Context menu (div absoluto) | `ContextMenu` — usa `onNodeContextMenu` de RF + shadcn |

### L3 (contenido interno): componentes standalone

Los editores (Monaco, markdown, JSON preview) no dependen de RF ni de shadcn. Son componentes puros que reciben `payload` y emiten `onContentMutate`.

---

## Patrones de reactflow.dev/examples a adoptar

| Ejemplo RF | Qué copiar | Para qué lo necesitamos |
|-----------|-----------|------------------------|
| Sub Flows | `parentId`, `extent: 'parent'`, `type: 'group'` | Documentos estructurados, nesting |
| Floating Edges | Ya lo tenemos — validar contra el ejemplo oficial | Aristas que conectan al punto más cercano |
| Edge Label Renderer | `<EdgeLabelRenderer>` para botones en aristas | Botón [x] para borrar aristas al hover |
| Context Menu | `onNodeContextMenu` + `onPaneContextMenu` | Menú de acciones por nodo (editar, borrar, duplicar) |
| Drag and Drop | `screenToFlowPosition` en `onDrop` | Arrastrar desde sidebar al canvas |
| Expand/Collapse | `hidden` property en nodos hijos | Colapsar grupos (precursor de ProxyEdge) |

### Ejemplo a NO adoptar

| Ejemplo RF | Por qué no |
|-----------|-----------|
| Undo and Redo | Guarda estado visual completo. Nuestro undo es semántico (Zustand). Un Ctrl+Z no debe deshacer un pan/zoom. |

---

## Docs relacionados

- `ARCHITECTURE.md` — Modelo de 3 capas
- `_meta/architecture_critique.md` — Problemas y recomendaciones
- `02_L2_graph_viewer/graph_foundations.md` — Estado canónico del editor
- `_legacy/2026-03-20-ui-plan-review-design.md` — Decisiones originales de diseño
