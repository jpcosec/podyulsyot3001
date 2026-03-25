# Catálogo de Patrones ReactFlow

> Patrones, ejemplos y componentes de ReactFlow aplicables al Node Editor. Cada entrada incluye código copiable y cómo mapea a nuestra arquitectura L1/L2/L3.

---

## Índice por prioridad de adopción

| Prioridad | Patrón | Capa | Sección |
|-----------|--------|------|---------|
| **Crítico** | Sub-Flows (parentId, groups) | L2 | [1](#1-sub-flows) |
| **Crítico** | elkjs Layout | L2 | [2](#2-elkjs-layout) |
| **Crítico** | Contextual Zoom (render tiers) | L2→L3 | [3](#3-contextual-zoom-render-tiers) |
| **Alto** | BaseNode + composición | L2 | [4](#4-basenode-sistema-de-composición) |
| **Alto** | LabeledGroupNode | L2 | [5](#5-labeled-group-node) |
| **Alto** | ButtonEdge (delete en arista) | L2 | [6](#6-button-edge) |
| **Alto** | Floating Edges | L2 | [7](#7-floating-edges) |
| **Alto** | Context Menu | L1→L2 | [8](#8-context-menu) |
| **Alto** | Drag and Drop (sidebar → canvas) | L1→L2 | [9](#9-drag-and-drop) |
| **Alto** | NodeToolbar | L2 | [10](#10-node-toolbar) |
| **Medio** | Connection Validation | L2 | [11](#11-connection-validation) |
| **Medio** | Save and Restore | L1 | [12](#12-save-and-restore) |
| **Medio** | Node Intersections | L2 | [13](#13-node-intersections) |
| **Medio** | Node Collisions | L2 | [14](#14-node-collisions) |
| **Medio** | Touch Device Support | L2 | [15](#15-touch-device) |
| **Bajo** | Whiteboard (rectangle drawing) | L2 | [16](#16-whiteboard-rectangles) |
| **Bajo** | Stress Test (performance baseline) | L2 | [17](#17-stress-test) |
| **Dev** | DevTools | L2 | [18](#18-devtools) |
| **UI Kit** | NodeAppendix, NodeTooltip, BaseHandle | L2→L3 | [19](#19-ui-kit-components) |
| **UI Kit** | DatabaseSchemaNode | L3 | [20](#20-database-schema-node) |

---

## 1. Sub-Flows

**Fuente:** `reactflow.dev/examples/grouping/sub-flows`
**Capa:** L2
**Prioridad:** CRÍTICO — requisito inmediato para documentos anidados

### Patrón clave

Los sub-flows usan tres propiedades en los nodos:

```typescript
// Nodo grupo (contenedor)
{
  id: '4',
  data: { label: 'Group B' },
  position: { x: 320, y: 200 },
  style: { width: 300, height: 300 },
  type: 'group',                        // ← tipo especial
}

// Nodo hijo (vive dentro del grupo)
{
  id: '4a',
  data: { label: 'Node B.1' },
  position: { x: 15, y: 65 },          // ← relativo al padre
  parentId: '4',                         // ← referencia al grupo
  extent: 'parent',                      // ← no puede salir del grupo
}

// Grupo anidado (grupo dentro de grupo)
{
  id: '4b',
  data: { label: 'Group B.A' },
  position: { x: 15, y: 120 },
  style: { backgroundColor: 'rgba(255, 0, 255, 0.2)', height: 150, width: 270 },
  parentId: '4',                         // ← hijo de Group B
}

// Nodo dentro del grupo anidado
{
  id: '4b1',
  data: { label: 'Node B.A.1' },
  position: { x: 20, y: 40 },
  parentId: '4b',                        // ← hijo de Group B.A (2 niveles)
}
```

### Cómo mapea a nuestro AST

```typescript
// ASTNode ya tiene parentId — solo falta:
// 1. type: 'group' para contenedores
// 2. extent: 'parent' para restringir movimiento
// 3. style.width/height para dimensiones del grupo

interface ASTNode {
  id: string;
  parentId?: string;         // ← ya lo tenemos
  isSubflow: boolean;        // ← mapea a type: 'group'
  // ...
}
```

### Edges entre niveles

ReactFlow soporta edges entre nodos de diferentes grupos nativamente:

```typescript
{ id: 'e2a-4a', source: '2a', target: '4a' }  // Group A → Group B
{ id: 'e4a-4b1', source: '4a', target: '4b1' } // nivel 1 → nivel 2 dentro del mismo grupo
```

### Lo que NO resuelve RF

- **Collapse/Expand** — RF no tiene toggle nativo. Hay que usar `hidden: true` en nodos hijos + crear ProxyEdges custom.
- **Tamaño automático del grupo** — RF requiere width/height explícitos. elkjs puede calcularlos.
- **Drag to reparent** — mover un nodo de un grupo a otro requiere lógica custom de detección + recálculo de posición relativa. (Es un Pro Example: `parent-child-relation`.)

---

## 2. elkjs Layout

**Fuente:** `reactflow.dev/examples/layout/elkjs`
**Capa:** L2
**Prioridad:** CRÍTICO — requerido para subflows anidados con layout automático

### Setup

```typescript
import ELK from 'elkjs/lib/elk.bundled.js';

const elk = new ELK();

const elkOptions = {
  'elk.algorithm': 'layered',
  'elk.layered.spacing.nodeNodeBetweenLayers': '100',
  'elk.spacing.nodeNode': '80',
};
```

### Función de layout

```typescript
const getLayoutedElements = async (nodes, edges, options = {}) => {
  const isHorizontal = options?.['elk.direction'] === 'RIGHT';

  const graph = {
    id: 'root',
    layoutOptions: { ...elkOptions, ...options },
    children: nodes.map((node) => ({
      id: node.id,
      width: node.measured?.width ?? 150,
      height: node.measured?.height ?? 50,
      // Para subflows: agregar children recursivamente
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layoutedGraph = await elk.layout(graph);

  return {
    nodes: nodes.map((node) => {
      const layoutedNode = layoutedGraph.children?.find((n) => n.id === node.id);
      return {
        ...node,
        position: { x: layoutedNode?.x ?? 0, y: layoutedNode?.y ?? 0 },
        sourcePosition: isHorizontal ? 'right' : 'bottom',
        targetPosition: isHorizontal ? 'left' : 'top',
      };
    }),
    edges,
  };
};
```

### Direcciones de layout

```typescript
// Vertical (top-down) — default para grafos de pipeline
{ 'elk.direction': 'DOWN' }

// Horizontal (left-right) — útil para timelines
{ 'elk.direction': 'RIGHT' }
```

### Para nuestro proyecto

- elkjs calcula posiciones incluyendo contenedores anidados — resuelve el problema de "tamaño automático del grupo"
- `elk.algorithm: 'layered'` es correcto para grafos DAG (nuestro caso principal)
- Para grafos más libres: `'elk.algorithm': 'force'` o `'stress'`
- **Web Worker:** NO necesario para <200 nodos. Evaluar cuando el grafo supere ese umbral.

---

## 3. Contextual Zoom (Render Tiers)

**Fuente:** `reactflow.dev/examples/interaction/contextual-zoom`
**Capa:** L2→L3
**Prioridad:** CRÍTICO — resuelve el problema de performance con nodos ricos

### El patrón

```typescript
import { useStore } from '@xyflow/react';

// Selector atómico — solo re-renderiza cuando cruza el threshold
const zoomSelector = (s) => s.transform[2] >= 0.9;

function ZoomNode({ data }) {
  const showContent = useStore(zoomSelector);

  return (
    <>
      <Handle type="target" position={Position.Left} />
      {showContent ? data.content : <Placeholder />}
      <Handle type="source" position={Position.Right} />
    </>
  );
}
```

### Cómo aplicar en nuestra arquitectura

Esto es exactamente el "render tier" que faltaba en la critique. El NodeShell (L2) decide qué renderizar:

```typescript
// NodeShell.tsx (L2)
const ZOOM_THRESHOLD_DETAIL = 0.9;
const ZOOM_THRESHOLD_LABEL = 0.4;

const zoomLevel = useStore((s) => {
  const zoom = s.transform[2];
  if (zoom >= ZOOM_THRESHOLD_DETAIL) return 'detail';
  if (zoom >= ZOOM_THRESHOLD_LABEL) return 'label';
  return 'dot';
});

function NodeShell({ data }) {
  switch (zoomLevel) {
    case 'detail':
      // L3 completo — editor, markdown, JSON preview
      return <InternalNodeRouter payload={data.payload} />;
    case 'label':
      // Solo título + icono de tipo
      return <NodeLabel title={data.payload.title} typeId={data.typeId} />;
    case 'dot':
      // Punto de color
      return <NodeDot token={data.visualToken} />;
  }
}
```

**Impacto:** Con 100 nodos, solo los 5-10 visibles a zoom alto renderizan Monaco/markdown. El resto renderiza un `<div>` de 2 elementos. Esto elimina el problema de "50 editores pesados en el DOM".

---

## 4. BaseNode (Sistema de composición)

**Fuente:** `reactflow.dev/ui/components/base-node`
**Capa:** L2
**Prioridad:** Alto — reemplaza nuestro NodeShell con un patrón composable estándar

### Componentes

```typescript
// BaseNode — contenedor con estados selected/hover
function BaseNode({ className, ...props }) {
  return (
    <div
      className={cn(
        "bg-card text-card-foreground relative rounded-md border",
        "hover:ring-1",
        "[.react-flow__node.selected_&]:border-muted-foreground",
        "[.react-flow__node.selected_&]:shadow-lg",
        className,
      )}
      tabIndex={0}
      {...props}
    />
  );
}

// Header — título + acciones
function BaseNodeHeader({ className, ...props }) {
  return (
    <header className={cn(
      "flex flex-row items-center justify-between gap-2 px-3 py-2",
      className
    )} {...props} />
  );
}

// Title — texto no seleccionable (feel de app nativa)
function BaseNodeHeaderTitle({ className, ...props }) {
  return <h3 className={cn("user-select-none flex-1 font-semibold", className)} {...props} />;
}

// Content — zona del payload L3
function BaseNodeContent({ className, ...props }) {
  return <div className={cn("flex flex-col gap-y-2 p-3", className)} {...props} />;
}

// Footer — acciones secundarias
function BaseNodeFooter({ className, ...props }) {
  return <div className={cn("flex flex-col items-center border-t px-3 pt-2 pb-3", className)} {...props} />;
}
```

### Uso como NodeShell

```typescript
function UniversalNodeShell({ data }) {
  const { astNode, themeTokens } = data;

  return (
    <BaseNode>
      <BaseNodeHeader>
        <BaseNodeHeaderTitle>{astNode.payload.title}</BaseNodeHeaderTitle>
        <TypeIcon typeId={astNode.typeId} />
      </BaseNodeHeader>
      <BaseNodeContent>
        <InternalNodeRouter payload={astNode.payload} />
      </BaseNodeContent>
    </BaseNode>
  );
}
```

### Por qué adoptarlo

- `tabIndex={0}` viene de fábrica → accesibilidad del teclado gratis
- Los selectores CSS `[.react-flow__node.selected_&]` manejan el estado de selección sin lógica custom
- Composición Header/Content/Footer en lugar de un blob monolítico

---

## 5. Labeled Group Node

**Fuente:** `reactflow.dev/ui/components/labeled-group-node`
**Capa:** L2
**Prioridad:** Alto — contenedores para subflows con label posicionable

### Componente

```typescript
function GroupNode({ label, position, ...props }) {
  return (
    <BaseNode className="bg-opacity-50 h-full overflow-hidden rounded-sm bg-white" {...props}>
      <Panel className="m-0 p-0" position={position}>
        {label && (
          <GroupNodeLabel className={getLabelClassName(position)}>
            {label}
          </GroupNodeLabel>
        )}
      </Panel>
    </BaseNode>
  );
}

function GroupNodeLabel({ children, className, ...props }) {
  return (
    <div className="h-full w-full" {...props}>
      <div className={cn("text-card-foreground bg-secondary w-fit p-2 text-xs", className)}>
        {children}
      </div>
    </div>
  );
}
```

### Para nuestro proyecto

Usa `<Panel position="top-left">` de RF para posicionar el label del grupo. Reemplaza los estilos hardcoded de `.react-flow__node-group` con un componente composable que se registra como `nodeTypes.group`.

---

## 6. Button Edge

**Fuente:** `reactflow.dev/ui/components/button-edge` + `reactflow.dev/examples/edges/custom-edges`
**Capa:** L2
**Prioridad:** Alto — borrar aristas sin seleccionar + Delete

### Componente

```typescript
import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from '@xyflow/react';

function ButtonEdge({
  sourceX, sourceY, targetX, targetY,
  sourcePosition, targetPosition,
  style = {}, markerEnd, children,
}: EdgeProps & { children: ReactNode }) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX, sourceY, sourcePosition,
    targetX, targetY, targetPosition,
  });

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={style} />
      <EdgeLabelRenderer>
        <div
          className="nodrag nopan pointer-events-auto absolute"
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
          }}
        >
          {children}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
```

### Uso

```typescript
// Registro
const edgeTypes = { button: ButtonEdge };

// En los datos
{
  id: 'e1-2',
  source: '1',
  target: '2',
  type: 'button',
  data: { /* cualquier dato para el label */ }
}

// El children se renderiza como botón
<ButtonEdge {...edgeProps}>
  <button onClick={() => deleteEdge(id)}>×</button>
</ButtonEdge>
```

### Clave técnica

`EdgeLabelRenderer` es un portal que renderiza HTML fuera del SVG. Sin esto, los eventos de clic no funcionan en botones sobre aristas SVG. Las clases `nodrag nopan` previenen que el clic en el botón inicie un drag del canvas.

---

## 7. Floating Edges

**Fuente:** `reactflow.dev/examples/edges/floating-edges`
**Capa:** L2
**Prioridad:** Alto — ya tenemos una implementación, validar contra la oficial

### Funciones helper

```typescript
// Calcula el punto de intersección entre el centro de dos nodos y el borde del nodo
function getNodeIntersection(intersectionNode, targetNode) {
  const { width: w2, height: h2 } = intersectionNode.measured;
  const pos = intersectionNode.internals.positionAbsolute;
  const targetPos = targetNode.internals.positionAbsolute;

  const w = w2 / 2;
  const h = h2 / 2;
  const x2 = pos.x + w;
  const y2 = pos.y + h;
  const x1 = targetPos.x + targetNode.measured.width / 2;
  const y1 = targetPos.y + targetNode.measured.height / 2;

  const xx1 = (x1 - x2) / (2 * w) - (y1 - y2) / (2 * h);
  const yy1 = (x1 - x2) / (2 * w) + (y1 - y2) / (2 * h);
  const a = 1 / (Math.abs(xx1) + Math.abs(yy1));
  const xx3 = a * xx1;
  const yy3 = a * yy1;

  return {
    x: w * (xx3 + yy3) + x2,
    y: h * (-xx3 + yy3) + y2,
  };
}

// Determina de qué lado del nodo sale/llega la arista
function getEdgePosition(node, intersectionPoint) {
  const n = { ...node.internals.positionAbsolute, ...node };
  const px = Math.round(intersectionPoint.x);
  const py = Math.round(intersectionPoint.y);

  if (px <= Math.round(n.x) + 1) return Position.Left;
  if (px >= Math.round(n.x) + n.measured.width - 1) return Position.Right;
  if (py <= Math.round(n.y) + 1) return Position.Top;
  return Position.Bottom;
}

// API pública
export function getEdgeParams(source, target) {
  const sourceIntersection = getNodeIntersection(source, target);
  const targetIntersection = getNodeIntersection(target, source);

  return {
    sx: sourceIntersection.x,
    sy: sourceIntersection.y,
    tx: targetIntersection.x,
    ty: targetIntersection.y,
    sourcePos: getEdgePosition(source, sourceIntersection),
    targetPos: getEdgePosition(target, targetIntersection),
  };
}
```

### Para nuestro proyecto

Comparar nuestra implementación actual (`getNodeIntersection`, `getFloatingEdgeParams`) contra este código oficial. Usa `node.internals.positionAbsolute` (API actual de RF) en lugar de calcular posiciones manualmente.

---

## 8. Context Menu

**Fuente:** `reactflow.dev/examples/interaction/context-menu`
**Capa:** L1→L2
**Prioridad:** Alto — reemplaza el connect menu manual

### Patrón

```typescript
const [menu, setMenu] = useState(null);
const ref = useRef(null);

const onNodeContextMenu = useCallback((event, node) => {
  event.preventDefault();

  // Posicionar inteligentemente para no salir de la pantalla
  const pane = ref.current.getBoundingClientRect();
  setMenu({
    id: node.id,
    top: event.clientY < pane.height - 200 && event.clientY,
    left: event.clientX < pane.width - 200 && event.clientX,
    right: event.clientX >= pane.width - 200 && pane.width - event.clientX,
    bottom: event.clientY >= pane.height - 200 && pane.height - event.clientY,
  });
}, []);

const onPaneClick = useCallback(() => setMenu(null), []);

return (
  <div ref={ref}>
    <ReactFlow
      onNodeContextMenu={onNodeContextMenu}
      onPaneClick={onPaneClick}
    >
      {menu && <ContextMenu onClick={onPaneClick} {...menu} />}
    </ReactFlow>
  </div>
);
```

### ContextMenu component

```typescript
function ContextMenu({ id, top, left, right, bottom, ...props }) {
  const { getNode, setNodes, addNodes, setEdges } = useReactFlow();

  const duplicateNode = useCallback(() => {
    const node = getNode(id);
    addNodes({
      ...node,
      id: `${node.id}-copy`,
      position: { x: node.position.x + 50, y: node.position.y + 50 },
    });
  }, [id, getNode, addNodes]);

  const deleteNode = useCallback(() => {
    setNodes((nodes) => nodes.filter((node) => node.id !== id));
    setEdges((edges) => edges.filter((edge) => edge.source !== id));
  }, [id, setNodes, setEdges]);

  return (
    <div style={{ top, left, right, bottom }} className="context-menu" {...props}>
      <button onClick={duplicateNode}>duplicate</button>
      <button onClick={deleteNode}>delete</button>
    </div>
  );
}
```

### Recomendación

Reemplazar este `<div>` con `shadcn/ui ContextMenu` para accesibilidad y posicionamiento via floating-ui. El patrón de RF maneja los eventos (`onNodeContextMenu`, `onPaneContextMenu`), shadcn maneja la UI.

---

## 9. Drag and Drop

**Fuente:** `reactflow.dev/examples/interaction/drag-and-drop`
**Capa:** L1→L2
**Prioridad:** Alto — arrastrar tipos de nodo desde sidebar al canvas

### Patrón completo (hook + sidebar + flow)

```typescript
// useDnD.tsx — hook con context
export function DnDProvider({ children }) {
  const [isDragging, setIsDragging] = useState(false);
  const [dropAction, setDropAction] = useState(null);

  return (
    <DnDContext.Provider value={{ isDragging, setIsDragging, dropAction, setDropAction }}>
      {children}
    </DnDContext.Provider>
  );
}

export const useDnD = () => {
  const { screenToFlowPosition } = useReactFlow();
  const { isDragging, setIsDragging, setDropAction, dropAction } = useContext(DnDContext);

  const onDragStart = useCallback((event, onDrop) => {
    event.preventDefault();
    event.target.setPointerCapture(event.pointerId);
    setIsDragging(true);
    setDropAction(onDrop);
  }, []);

  const onDragEnd = useCallback((event) => {
    event.target.releasePointerCapture(event.pointerId);
    const elementUnderPointer = document.elementFromPoint(event.clientX, event.clientY);
    const isDroppingOnFlow = elementUnderPointer?.closest('.react-flow');

    if (isDroppingOnFlow) {
      const flowPosition = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      dropAction?.({ position: flowPosition });
    }
    setIsDragging(false);
  }, [screenToFlowPosition, dropAction]);

  useEffect(() => {
    if (!isDragging) return;
    document.addEventListener('pointerup', onDragEnd);
    return () => document.removeEventListener('pointerup', onDragEnd);
  }, [onDragEnd, isDragging]);

  return { isDragging, onDragStart };
};
```

### Sidebar

```typescript
function Sidebar() {
  const { onDragStart } = useDnD();
  const { setNodes } = useReactFlow();

  const createNode = (type) => ({ position }) => {
    setNodes((nds) => nds.concat({
      id: crypto.randomUUID(),
      type,
      position,
      data: { label: `${type} node` },
    }));
  };

  return (
    <aside>
      <div onPointerDown={(e) => onDragStart(e, createNode('input'))}>
        Input Node
      </div>
      <div onPointerDown={(e) => onDragStart(e, createNode('default'))}>
        Default Node
      </div>
    </aside>
  );
}
```

### Clave

Usa `screenToFlowPosition` para convertir coordenadas de pantalla a coordenadas del canvas (respetando zoom y pan). El pattern usa pointer events (no HTML drag API) para funcionar en touch y desktop.

---

## 10. Node Toolbar

**Fuente:** `reactflow.dev/examples/nodes/node-toolbar`
**Capa:** L2
**Prioridad:** Alto — acciones rápidas sobre nodos seleccionados

### Patrón

```typescript
import { NodeToolbar, Position } from '@xyflow/react';

function NodeWithToolbar({ data }) {
  return (
    <>
      <NodeToolbar
        isVisible={data.forceToolbarVisible || undefined}  // undefined = auto (show on select)
        position={data.toolbarPosition ?? Position.Top}
        align="center"
      >
        <button>cut</button>
        <button>copy</button>
        <button>paste</button>
      </NodeToolbar>
      <div>{data.label}</div>
    </>
  );
}
```

### Props clave

- `isVisible`: `undefined` = aparece solo cuando el nodo está seleccionado. `true` = siempre visible.
- `position`: `Position.Top | Right | Bottom | Left`
- `align`: `'start' | 'center' | 'end'`
- La toolbar no escala con el zoom — siempre legible.

---

## 11. Connection Validation

**Fuente:** `reactflow.dev/examples/interaction/validation`
**Capa:** L2
**Prioridad:** Medio — prevenir conexiones inválidas antes de crearlas

### Patrón

```typescript
const isValidConnection = (connection) => {
  // Ejemplo: solo permitir conexiones al nodo 'B'
  return connection.target === 'B';

  // Ejemplo real: validar por tipo de nodo
  // const sourceNode = getNode(connection.source);
  // const targetNode = getNode(connection.target);
  // return schema.allowedConnections[sourceNode.type]?.includes(targetNode.type);
};

<ReactFlow
  isValidConnection={isValidConnection}
  // RF muestra visual feedback:
  // .react-flow__handle.valid → verde
  // .react-flow__handle.connectingto → rojo (inválido)
/>
```

### Para nuestro proyecto

El schema de representación define `allowed_relations` por tipo de nodo. La función de validación consulta el schema:

```typescript
const isValidConnection = (connection) => {
  const source = getNode(connection.source);
  const target = getNode(connection.target);
  return registry.canConnect(source.data.typeId, target.data.typeId);
};
```

---

## 12. Save and Restore

**Fuente:** `reactflow.dev/examples/interaction/save-and-restore`
**Capa:** L1
**Prioridad:** Medio — serialización del estado visual

### Patrón

```typescript
const [rfInstance, setRfInstance] = useState(null);

// Guardar
const onSave = () => {
  const flow = rfInstance.toObject();  // { nodes, edges, viewport }
  localStorage.setItem(flowKey, JSON.stringify(flow));
};

// Restaurar
const onRestore = () => {
  const flow = JSON.parse(localStorage.getItem(flowKey));
  if (flow) {
    setNodes(flow.nodes || []);
    setEdges(flow.edges || []);
    setViewport({ x: flow.viewport.x, y: flow.viewport.y, zoom: flow.viewport.zoom });
  }
};

<ReactFlow onInit={setRfInstance} />
```

### Para nuestro proyecto

`rfInstance.toObject()` serializa todo: nodos, edges, viewport. Útil para guardar view presets (layout_presets.md). **NO usar para persistencia de datos de dominio** — el AST de dominio se persiste por separado vía L1.

---

## 13. Node Intersections

**Fuente:** `reactflow.dev/examples/nodes/intersections`
**Capa:** L2
**Prioridad:** Medio — útil para drag-to-reparent y detección de drop zones

### Patrón

```typescript
const { getIntersectingNodes } = useReactFlow();

const onNodeDrag = useCallback((_, node) => {
  const intersections = getIntersectingNodes(node).map((n) => n.id);

  setNodes((ns) =>
    ns.map((n) => ({
      ...n,
      className: intersections.includes(n.id) ? 'highlight' : '',
    }))
  );
}, []);

<ReactFlow onNodeDrag={onNodeDrag} selectNodesOnDrag={false} />
```

### Para nuestro proyecto

Combinado con subflows: cuando arrastras un nodo sobre un grupo, `getIntersectingNodes` detecta el grupo y lo resalta. Al soltar, reparentas el nodo. Es la base para el patrón "drag to reparent" del Pro Example.

---

## 14. Node Collisions

**Fuente:** `reactflow.dev/examples/layout/node-collisions`
**Capa:** L2
**Prioridad:** Medio — prevenir nodos superpuestos después de layout manual

### Algoritmo

```typescript
const resolveCollisions = (nodes, { maxIterations = 50, margin = 0 }) => {
  const boxes = getBoxesFromNodes(nodes, margin);

  for (let iter = 0; iter <= maxIterations; iter++) {
    let moved = false;
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        // Detectar overlap
        // Resolver moviéndose por el eje de menor solapamiento
      }
    }
    if (!moved) break;
  }
  return newNodes;
};

// Disparar después de drag
<ReactFlow onNodeDragStop={(_, node) => {
  setNodes(resolveCollisions(nodes));
}} />
```

### Para nuestro proyecto

Útil como post-procesamiento después de que elkjs calcule el layout, o cuando el usuario mueve un nodo manualmente a una posición que causa overlap.

---

## 15. Touch Device

**Fuente:** `reactflow.dev/examples/interaction/touch-device`
**Capa:** L2
**Prioridad:** Medio

### Patrón

```css
/* Handles más grandes para touch */
.react-flow.touch-flow .react-flow__handle {
  width: 20px;
  height: 20px;
}

/* Animación de bounce cuando se está conectando */
@keyframes bounce {
  0% { transform: var(--translate) scale(1); }
  50% { transform: var(--translate) scale(1.1); }
}
.react-flow.touch-flow .react-flow__handle.clickconnecting {
  animation: bounce 1600ms infinite ease-in;
}
```

RF soporta `connectOnClick` de fábrica — tap en handle source, tap en handle target = conexión. Solo hay que hacer los handles suficientemente grandes.

---

## 16. Whiteboard (Rectangles)

**Fuente:** `reactflow.dev/examples/whiteboard/rectangle`
**Capa:** L2
**Prioridad:** Bajo — futuro: crear nodos dibujando en el canvas

### Patrón clave

```typescript
// RectangleTool — captura pointer events sobre el canvas
function RectangleTool({ onAdd }) {
  const { screenToFlowPosition } = useReactFlow();

  const onPointerDown = (e) => {
    const start = screenToFlowPosition({ x: e.clientX, y: e.clientY });
    // Track drag...
  };

  const onPointerUp = (e) => {
    const end = screenToFlowPosition({ x: e.clientX, y: e.clientY });
    onAdd({
      id: crypto.randomUUID(),
      type: 'rectangle',
      position: { x: Math.min(start.x, end.x), y: Math.min(start.y, end.y) },
      style: { width: Math.abs(end.x - start.x), height: Math.abs(end.y - start.y) },
    });
  };

  return <div className="nopan nodrag" onPointerDown={onPointerDown} />;
}
```

Mode switching entre "select" y "draw" — las clases `nopan nodrag` previenen que el pointer event se interprete como pan/drag del canvas.

---

## 17. Stress Test

**Fuente:** `reactflow.dev/examples/nodes/stress`
**Capa:** L2
**Prioridad:** Bajo — benchmark de referencia

450 nodos (15×30 grid) + edges. RF lo maneja sin problemas.

### Patrón para randomizar posiciones (útil para testing)

```typescript
const updatePos = () => {
  setNodes((nds) =>
    nds.map((node) => ({
      ...node,
      position: { x: Math.random() * 1500, y: Math.random() * 1500 },
    }))
  );
};
```

**Referencia:** si 450 nodos con nodos simples van bien, con render tiers (contextual zoom) deberíamos manejar 1000+ nodos siempre que solo los enfocados rendericen contenido L3 completo.

---

## 18. DevTools

**Fuente:** `reactflow.dev/ui/components/devtools`
**Capa:** L2
**Prioridad:** Dev — adoptar inmediatamente para desarrollo

### Componentes

```typescript
import { DevTools } from './devtools';

<ReactFlow>
  <DevTools position="top-left" />
</ReactFlow>
```

Tres herramientas toggleables:

1. **ViewportLogger** — muestra x, y, zoom en tiempo real
2. **NodeInspector** — renderiza debajo de cada nodo su id, type, position, dimensions, data (usando `ViewportPortal`)
3. **ChangeLogger** — intercepta `onNodesChange` y loguea cada cambio (add, remove, position, dimensions, select)

### El source completo usa

- `useStore` para viewport
- `useStoreApi` para interceptar `onNodesChange`
- `ViewportPortal` para renderizar labels que se mueven con el canvas
- `useNodes` + `getInternalNode` para inspección
- `shadcn/ui ToggleGroup` para la UI

### Para nuestro proyecto

Copiar tal cual durante desarrollo. El `ChangeLogger` es especialmente útil para debugging del sistema de historial semántico — permite ver qué cambios emite RF vs qué acciones captura nuestro Zustand.

---

## 19. UI Kit Components

### BaseHandle

```typescript
function BaseHandle({ className, children, ...props }) {
  return (
    <Handle
      {...props}
      className={cn(
        "h-[11px] w-[11px] rounded-full border border-slate-300 bg-slate-100 transition",
        "dark:border-secondary dark:bg-secondary",
        className,
      )}
    >
      {children}
    </Handle>
  );
}
```

Reemplaza los handles default con handles estilizados + dark mode.

### NodeAppendix

```typescript
// Posiciona contenido absolutamente fuera del nodo
const appendixVariants = cva(
  "absolute flex w-full flex-col items-center rounded-md border bg-card p-1",
  {
    variants: {
      position: {
        top: "-translate-y-full -my-1",
        bottom: "top-full my-1",
        left: "-left-full -mx-1",
        right: "left-full mx-1",
      },
    },
  },
);

function NodeAppendix({ children, position, className, ...props }) {
  return (
    <div className={cn(appendixVariants({ position }), className)} {...props}>
      {children}
    </div>
  );
}
```

Útil para: badges de estado, contadores, metadata que no cabe en el nodo.

### NodeTooltip

Wrapper sobre `NodeToolbar` que aparece en hover (no solo en selección):

```typescript
<NodeTooltip>
  <NodeTooltipContent position={Position.Top}>
    Tooltip content
  </NodeTooltipContent>
  <BaseNode>
    <NodeTooltipTrigger>Hover me</NodeTooltipTrigger>
  </BaseNode>
</NodeTooltip>
```

---

## 20. Database Schema Node

**Fuente:** `reactflow.dev/ui/components/database-schema-node`
**Capa:** L3
**Prioridad:** UI Kit — template para nodos tipo tabla/schema

### Componentes

```typescript
// Compone BaseNode + shadcn Table
<DatabaseSchemaNode>
  <DatabaseSchemaNodeHeader>users</DatabaseSchemaNodeHeader>
  <DatabaseSchemaNodeBody>
    <DatabaseSchemaTableRow>
      <LabeledHandle id="id" title="id" type="target" position={Position.Left} />
      <DatabaseSchemaTableCell className="pl-0 pr-6 font-light">
        uuid
      </DatabaseSchemaTableCell>
    </DatabaseSchemaTableRow>
  </DatabaseSchemaNodeBody>
</DatabaseSchemaNode>
```

### Para nuestro proyecto

Este es un template directo para nodos L3 que muestran datos tabulares (ej. atributos de un Job Posting, skills de un CV). Cada fila tiene handles con IDs únicos, permitiendo conectar campos individuales entre nodos — no solo nodo a nodo.

---

## Resumen: Qué adoptar y en qué orden

### Fase 1 — Fundamentos (bloquean todo lo demás)

1. **Sub-Flows** — `parentId`, `type: 'group'`, `extent: 'parent'`
2. **elkjs** — layout automático con compound nodes
3. **BaseNode** — reemplazar NodeShell con sistema composable
4. **LabeledGroupNode** — registrar como `nodeTypes.group`
5. **DevTools** — durante desarrollo

### Fase 2 — Interacción core

6. **Contextual Zoom** — render tiers (crítico para performance)
7. **ButtonEdge** — borrar aristas interactivamente
8. **Context Menu** — RF events + shadcn ContextMenu
9. **NodeToolbar** — cut/copy/paste/delete sobre nodos
10. **Connection Validation** — `isValidConnection` desde el schema

### Fase 3 — Features

11. **Drag and Drop** — sidebar → canvas
12. **Floating Edges** — validar nuestra implementación vs oficial
13. **Node Intersections** — drag-to-reparent
14. **Save and Restore** — view presets
15. **Node Collisions** — post-layout de seguridad

### Fase 4 — Polish

16. **Touch Device** — handles grandes + connectOnClick
17. **BaseHandle, NodeAppendix, NodeTooltip** — UI kit
18. **DatabaseSchemaNode** — template para nodos tabulares

---

## Docs relacionados

- `_meta/reactflow_inventory.md` — Inventario actual RF vs custom
- `_meta/architecture_critique.md` — Problemas y recomendaciones
- `ARCHITECTURE.md` — Modelo de 3 capas
- `02_L2_graph_viewer/graph_foundations.md` — Estado canónico del editor
