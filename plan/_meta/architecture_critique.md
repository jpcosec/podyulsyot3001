# Crítica Arquitectónica: El Modelo de 3 Capas

> Análisis honesto de fortalezas, debilidades, contradicciones y riesgos de la arquitectura actual del Node Editor.

---

## Lo que funciona bien

**La separación L1/L2/L3 es sólida como modelo mental.** Mapea directamente al árbol de componentes React y da un vocabulario claro para discutir dónde vive cada responsabilidad. La metáfora Matrioshka es fácil de internalizar.

**Data Down / Events Up es el patrón correcto.** Unidireccionalidad estricta previene los ciclos de estado que destruyen proyectos React. Los contratos TypeScript entre capas hacen explícito lo que de otra forma sería acoplamiento implícito.

**El AST como representación intermedia es la decisión clave.** Sin esto, el canvas sería una extensión de la lógica de negocio. Con esto, el canvas es reutilizable entre dominios (CV, Job, Code IDE). Es lo que convierte al editor de "un componente" a "una plataforma".

---

## Problemas estructurales

### 1. El payload es `any` — el contrato central está roto

```typescript
payload: Record<string, any>;  // Contrato B
contentData: any;               // ASTNode.payload
```

El punto entero de definir contratos en TypeScript es type safety. Pero el dato más importante del sistema — lo que el nodo muestra y edita — es `any`. L2 pasa un blob opaco a L3, y L3 hace un `switch` sobre un string para decidir qué hacer. Esto significa:

- **No hay validación en compile time** de que el payload matchea el contentType
- **Cada nuevo tipo de contenido** requiere modificar el switch en `InternalNodeRouter`
- **Un payload malformado** crashea L3 silenciosamente

**Recomendación:** Discriminated union con payload tipado por contentType:

```typescript
type NodePayload =
  | { contentType: 'markdown'; content: string }
  | { contentType: 'tags'; tags: TagItem[] }
  | { contentType: 'json'; data: JsonValue; schema?: JsonSchema }
  | { contentType: 'image'; src: string; annotations?: Anchor[] };
```

### 2. contentType es una enumeración cerrada que viola el aislamiento

El contrato dice que L2 no conoce L3. Pero `contentType: 'markdown' | 'tag-editor' | 'image'` es una lista de capacidades de L3 viviendo en la interfaz de L2. Cada vez que L3 gana un nuevo tipo de editor, L2 tiene que saber de su existencia.

Esto es exactamente el problema que el Node Type Registry (`01b_node_type_registry_and_modes.md`) intenta resolver — pero el contrato actual no lo refleja. El contrato y el registry se diseñaron en paralelo sin reconciliarse.

**Recomendación:** El registry resuelve esto si se adopta como la fuente de verdad. L2 no necesita un switch — le pasa el `type_id` al registry y el registry retorna el renderer. El contrato entre L2 y L3 se reduce a:

```typescript
interface CanvasToNodeProps {
  nodeId: string;
  typeId: string;        // registry lookup, no enum
  isFocused: boolean;
  payload: unknown;      // validado por el registry en runtime
}
```

### 3. `schemaToGraph()` es una función con tres trabajos

El doc de schema_translation describe tres fases:
1. Node Matching (identidad)
2. Topology Resolution (espacio)
3. Edge Resolution (conexiones)

Pero se presenta como una sola función: `schemaToGraph(rawData, schema)`. Esto va a crecer hasta ser inmanejable porque:

- **No se puede testear cada fase por separado**
- **No se puede reusar una fase** (ej. re-resolver edges sin re-matchear nodos)
- **Los errores de una fase se propagan silenciosamente** a la siguiente

**Recomendación:** Pipeline explícito con tipos intermedios:

```typescript
const matched = matchNodes(rawData, schema.node_types);     // MatchedNode[]
const topology = resolveTopology(matched, schema.topology);  // TopologyGraph
const ast = resolveEdges(topology, schema.edge_types);       // AST
```

### 4. dagre vs elkjs — el contrato ya está desactualizado

`ARCHITECTURE.md` define:
```typescript
layoutEngine: 'dagre' | 'manual';
```

Pero `_legacy/2026-03-20-ui-plan-review-design.md` decidió:
> "elkjs from the start. No dagre."

Y `01a_layout_and_view_presets.md` dice:
> "keep dagre for MVP, add elkjs later"

Tres documentos, tres respuestas. El contrato ya nació inconsistente.

**Recomendación:** Tomar la decisión una vez, en un solo lugar, y que el contrato la refleje. Si elkjs es el target, el contrato debería ser `layoutEngine: 'elk' | 'manual'` y dagre debería documentarse como legacy/transitorio.

### 5. Undo/Redo cruza capas sin contrato

El flow contract describe:
- L3 emite `onContentMutate` → L2 lo mete en `useGraphHistory()` → L2 emite `onTopologyMutate` → L1 recibe

Pero `01c_editor_state_and_history_contract.md` define semantic actions como "edit node payload", "create relation", etc.

Pregunta sin respuesta: **¿Quién es dueño del undo?**

- Si L3 tiene un editor Monaco con su propio undo (Ctrl+Z deshace un carácter), ¿eso dispara `onContentMutate` con cada undo interno?
- Si L2 tiene history de topología y L3 tiene history de contenido, Ctrl+Z tiene **dos significados distintos** dependiendo del foco.
- Si el usuario hace undo en L2 de un "edit payload", ¿L3 se entera? ¿Se resetea el editor interno?

**Recomendación:** Definir explícitamente la frontera: L3 maneja undo de **edición local** (keystroke-level). L2 maneja undo de **acciones semánticas** (node created, edge deleted, payload committed). La transición ocurre en `onContentMutate` — ese es el punto donde la edición local se convierte en acción semántica. Documentar que Ctrl+Z en L3-focused es local, Ctrl+Z en canvas-focused es semántico.

### 6. No hay modelo de error

Los contratos definen el happy path. No hay respuesta para:

- `schemaToGraph()` recibe datos que no matchean ninguna regla → ¿AST vacío? ¿Error? ¿Nodos "huérfanos"?
- Un payload llega malformado a L3 → ¿crash? ¿fallback a empty? ¿error boundary?
- La API falla durante un save → ¿el AST en memoria diverge del backend? ¿optimistic update? ¿rollback?
- El schema tiene reglas contradictorias → ¿primera gana? ¿excepción?

Esto importa especialmente porque el sistema planea ser **multi-dominio**. Cada schema nuevo es una fuente nueva de edge cases.

**Recomendación:** Agregar al contrato: `ASTValidationResult` como output alternativo de `schemaToGraph()`, y un error boundary pattern para L3 que renderiza un fallback visual (ej. "payload inválido para este tipo") en lugar de crashear el canvas entero.

### 7. La regla de aislamiento se rompe con features reales

"L1 no habla con L3" es elegante en papel. Pero considerar:

- **Selection sync:** L1 sidebar muestra detalles del nodo seleccionado. El contenido detallado vive en L3. ¿L1 lee el payload del AST directamente, o necesita que L3 le "cuente" qué tiene? Si lee el AST, está leyendo datos que L3 es responsable de mutar — shared state implícito.

- **Drag-and-drop externo:** El usuario arrastra un archivo desde el explorador (L1) hacia un nodo (L3). Este evento cruza L1 → L2 → L3, pero L2 no entiende "archivos" — solo topología. ¿L2 hace passthrough de eventos de drop?

- **Global keyboard shortcuts:** Ctrl+B para bold en el editor markdown (L3). Pero Ctrl+B en L1 podría significar "toggle sidebar". ¿Quién gana? El foco del DOM decide, no la arquitectura.

- **Validación cruzada:** "Este nodo requiere al menos 3 tags" es una regla de negocio (L1), pero se manifiesta en la UI del editor (L3). ¿L1 pasa reglas de validación como props a L3 a través de L2?

**Recomendación:** No abandonar la regla, pero documentar los **escape hatches legítimos**: React Context para estado de selección (read-only desde L3), event bus para drag-drop cross-layer, focus management como concern transversal fuera de las 3 capas.

### 8. El schema es un DSL que va a crecer sin control

El schema de traducción ya tiene: `match_rule`, `node_types`, `edge_types`, `render_as`, `color_token`, `visual_encoding`, `target_array`. Cada dominio nuevo necesitará reglas nuevas. No hay:

- **Versionado del schema** — ¿qué pasa cuando la estructura cambia?
- **Validación del schema** — ¿cómo saber si un schema es válido antes de pasarlo a `schemaToGraph()`?
- **Documentación del schema** — cada campo, qué acepta, qué pasa si falta
- **Migración** — schemas viejos con datos existentes

**Recomendación:** JSON Schema para validar los representation schemas. Versión explícita (`"schema_version": "1.0"`). Función `validateSchema()` que corre antes de `schemaToGraph()`.

---

## Dificultades de implementación previsibles

### Performance con nodos ricos

ReactFlow renderiza **todos** los nodos en el DOM. Si cada nodo contiene un Monaco editor, un markdown renderer, o una tabla editable, 50 nodos = 50 editores pesados. El doc legacy menciona "render tiers" pero la arquitectura no tiene un hook para esto.

Necesitará: virtualización de contenido L3 (solo el nodo enfocado renderiza el editor completo, el resto renderiza un preview estático), o React Flow's `nodeExtent` + viewport culling agresivo.

### La serialización inversa (AST → dominio) no está diseñada

`schemaToGraph()` va en una dirección. Pero cuando el usuario edita el grafo y guarda, necesitas `graphToSchema()` o `astToDomain()`. Esto es **más difícil** que el parsing original porque:

- El usuario puede haber creado nodos que no existían en el dominio original
- El usuario puede haber cambiado topología (nuevas edges) que implican relaciones de negocio
- No toda mutación del AST es válida en el dominio

No hay un solo doc que aborde esto. El flow contract solo dice "app toma el AST, lo convierte a Cypher y lo envía al backend."

### SubFlow collapse es un problema de estado distribuido

Cuando un grupo se colapsa: edges internas desaparecen, se crean ProxyEdges, el layout recalcula, el estado de los nodos internos debe preservarse (para re-expand), y el undo debe poder revertirlo. Esto toca L1 (collapsed state en view preset), L2 (ProxyEdges, layout), y L3 (los nodos internos que "desaparecen" pero siguen en el AST).

El doc `02_structured_documents_and_subflows.md` dice "strong fit with React Flow subflows" — pero React Flow's built-in subflow support es bastante limitado para este caso de uso. Los ProxyEdges son custom, el collapse state es custom, y la interacción entre collapsed groups y layout engines es donde elkjs se vuelve necesario.

### Persistencia fragmentada no es un problema técnico — es un problema de confianza

El status matrix muestra "persistence is fragmented between sandbox-local and CV-graph API." Pero el problema real es: si el usuario hace cambios en el grafo, ¿puede confiar en que se guardan? ¿Dónde? ¿Se puede recuperar un estado anterior?

La arquitectura no tiene respuesta para auto-save, conflict detection, o dirty state indication. Estos no son features — son requisitos de confianza del usuario.

---

## Contradicciones entre documentos

| Doc A dice | Doc B dice | Problema |
|-----------|-----------|----------|
| ARCHITECTURE: `layoutEngine: 'dagre' \| 'manual'` | Legacy review: "elkjs from the start, no dagre" | Contrato nació desactualizado |
| flow_contract: comunicación estricta a 1 paso | implementation_example: `NodeShell` importa `InternalNodeRouter` directamente | L2 importando L3 — ¿es esto "1 paso" o acoplamiento directo? |
| ARCHITECTURE: orden de implementación L2→L3→L1 | graph_foundations: status "partial", depends on status_matrix | L2 no puede estabilizarse sin decisiones de L1 (schema, persistence) |
| node_types: registry con `payload_schema` por tipo | flow_contract: `payload: Record<string, any>` | El registry promete tipado que el contrato no puede enforcing |
| layout_presets: "keep dagre for MVP" | legacy review: "elkjs from the start" | Contradicción directa sobre estrategia de layout |

---

## Resumen: Qué resolver antes de implementar

1. **Tipar el payload** — discriminated union, no `any`
2. **Reconciliar el Node Type Registry con los contratos** — el registry debería ser la fuente de verdad para tipos de nodo, no el enum en el contrato
3. **Diseñar la serialización inversa** (`astToDomain`) antes de implementar edición
4. **Decidir dagre vs elkjs** una sola vez, actualizar todos los docs
5. **Definir la frontera de undo** entre L3 (local) y L2 (semántico)
6. **Agregar modelo de error** a los contratos y a `schemaToGraph()`
7. **Documentar los escape hatches** del aislamiento estricto (context, event bus, focus)
