# Plan de Implementacion Front-end: Node Editor (Nodo a Nodo)

> Status note (2026-03-20): this is an implementation plan snapshot, not a current-status mirror. Parts of this plan are already implemented, and other assumptions may no longer match the active sandbox exactly.


## 1. Objetivo

Implementar un editor de grafos en React Flow para mapeo nodo a nodo, siguiendo la especificacion de interaccion definida en `docs/architecture/node_editor_behavior_spec.md`, con una ruta de sandbox dedicada para validar UX antes de integrar datos reales.

## 2. Alcance de esta fase

- Incluye:
  - Workspace fullscreen (canvas + sidebar colapsable)
  - Maquina de estados (`browse`, `focus`, `edit_node`, `edit_relation`)
  - Flujo drag-to-connect con menu contextual flotante
  - Modal tipado para edicion de propiedades
  - Paleta de creacion, filtros, minimapa y controles globales
  - Auto-layout manual por accion de usuario
- Excluye:
  - Colaboracion multiusuario
  - Permisos avanzados
  - Persistencia productiva final (solo wiring de capa de aplicacion)

## 3. Arquitectura recomendada

### 3.1 Motor de grafo

- `@xyflow/react` como motor base.
- `nodeTypes` y `edgeTypes` definidos a nivel modulo (referencias estables, no inline).

### 3.2 Estado

- Recomendado: store con slices separados:
  - `graphSlice` (nodes, edges, cambios y conexiones)
  - `editorSlice` (modo, seleccion, focus, dirty, overlays)
  - `uiSlice` (sidebar, filtros, mapeo visual)
- Regla clave: no mezclar estado de formulario modal con estado de posicionamiento del grafo.

### 3.3 Formularios tipados

- `react-hook-form` + `zod` con `discriminatedUnion` por tipo de nodo.
- `reset()` al abrir modal para sincronizar datos del nodo seleccionado.
- `useWatch` en subcomponentes para campos condicionales y evitar re-renders globales.

### 3.4 Overlays

- Modal de edicion fuera del canvas (portal), con backdrop y foco bloqueado.
- Menu flotante contextual anclado a coordenadas reales de suelta.
- Edicion de edge via overlay sobre la arista (etiqueta interactiva).

## 4. Modelo de componentes

- `GraphWorkspace` (layout fullscreen + composicion general)
- `GraphCanvas` (ReactFlow + handlers + viewport)
- `GraphSidebar` (controles globales, paleta, filtros, minimapa)
- `FloatingConnectMenu` (flujo drag-to-connect)
- `NodeEditModal` (edicion tipada de nodo)
- `EdgeEditPanel` (edicion de atributos de relacion)
- `nodes/StandardNode`, `nodes/ContainerNode`, `nodes/ChildNode`
- `edges/RelationEdge` (render y acciones de relacion)

## 5. Maquina de estados (contrato UX)

- `browse`: navegacion libre, hover, drag en nodos libres.
- `focus`: nodo centrado/zoom + no relacionados atenuados o ocultos + no interactivos.
- `edit_node`: modal tipado activo, canvas bloqueado.
- `edit_relation`: panel de relacion activo, canvas bloqueado segun politica.

Transiciones minimas:

- click nodo: `browse -> focus`
- doble click nodo o boton Editar: `focus -> edit_node`
- click edge: `focus|browse -> edit_relation`
- fondo vacio: `focus -> browse`
- guardar/descartar: `edit_* -> focus`

Guard rule:

- no salida de `edit_node/edit_relation` con cambios sin resolver (guardar o descartar).

## 6. Flujo drag-to-connect

1. `onConnectStart` guarda nodo origen y handle.
2. `onConnectEnd`:
   - si cae sobre nodo valido: conectar directo
   - si cae en canvas vacio: abrir `FloatingConnectMenu`
3. En menu:
   - elegir nodo existente -> crear relacion
   - `+ Crear Nuevo` -> abrir modal, crear nodo, conectar
   - click fuera -> cancelar

## 7. Sidebar (centro de mando)

Secciones minimas:

1. Estado actual (modo + nodo/relacion activa)
2. Dirty + acciones (`Save Workspace`, `Discard/Reset`, `Unfocus`, `Auto-Layout`)
3. Paleta de creacion (drag and drop al canvas)
4. Filtros y capas (tipos de relacion, busqueda, filtros por atributos)
5. Mapeo visual (categoria -> color/shape, tipo relacion -> estilo)
6. Minimap

## 8. Mapeo visual explicito

Contrato configurable desde UI:

- Nodo:
  - categoria -> color
  - tipo -> forma
  - estado -> borde/opacidad
- Relacion:
  - tipo -> color/linea/animacion

Todo cambio de mapeo debe reflejarse en canvas inmediatamente.

## 9. Auto-layout

- Estrategia inicial:
  - `dagre` para fase MVP (rapido, simple)
  - opcion futura a `elkjs` para casos complejos
- Auto-layout solo por accion explicita del usuario (`Auto-Layout`), no en cada render.

## 10. Plan de implementacion por iteraciones

### Iteracion 1: Workspace + estado base

- Crear route dedicada de sandbox
- Render fullscreen, canvas base, sidebar colapsable
- Implementar estado `browse/focus`

### Iteracion 2: Nodos y relaciones base

- Custom nodes y edges
- Hover, seleccion, focus visual
- Filtros por tipo de relacion
- Composicion visible: contenedores colapsados/expandidos con hijos vinculados

### Iteracion 3: Edit node modal tipado

- RHF + Zod
- Campos por tipo (`string`, `text`, `number`, `date`, `boolean`, `enum`, `enum_open`)
- Dirty/save/discard con guard rule

### Iteracion 4: Edit relation + drag-to-connect

- Panel de edge editable
- `onConnectStart/onConnectEnd` + menu contextual flotante
- Crear nuevo nodo desde menu y conectar automaticamente

### Iteracion 5: Paleta + auto-layout + hardening

- DnD desde sidebar
- Auto-layout por boton
- Optimizaciones de rendimiento (memo/selectores)

## 11. Criterios de aceptacion

- Modo `focus` centra y limita interaccion en no relacionados.
- Modal tipado valida y bloquea guardado en error.
- Estado dirty se activa con cambios reales y se limpia al guardar/descartar.
- Drag-to-connect en canvas vacio abre menu contextual en coordenada correcta.
- Seleccion de nodo existente o nuevo desde menu cierra flujo y crea relacion.
- Filtros/capas y mapeo visual actualizan canvas en tiempo real.
- `Auto-Layout` reordena sin perder consistencia de edges.
- Nodos contenedor muestran contador en estado colapsado y revelan hijos al expandir.

## 12. Riesgos y mitigaciones

- Re-render excesivo en grafo grande:
  - Mitigar con selectores finos, `React.memo`, callbacks estables.
- Conflicto de z-index overlays:
  - Mitigar con portales para modal/menu/panel edge.
- Estado duplicado nodes/edges:
  - Mantener fuente unica en store.
- Complejidad de esquema dinamico:
  - Discriminated unions por tipo + normalizacion de datos de entrada.

## 13. Sandbox route obligatoria

- Ruta dedicada para esta fase: `/sandbox/node_editor`.
- Debe funcionar sin datos reales ni dependencias de backend.
- Su objetivo es alinear implementacion y criterios de aceptacion antes de desarrollar la version productiva.
