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

**Recomendación:** No abandonar la regla, pero documentar los **escape hatches legítimos** — con cuidado de no crear problemas nuevos:

- **Estado compartido cross-layer:** NO usar React Context genérico. Un `SelectionContext` que cambia con cada clic causará re-render de los 100 nodos L3 que lo consumen. La solución performante son **selectores atómicos** (Zustand ya está en el proyecto): `useStore(state => state.selectedNodeId === myId)` — cada nodo solo re-renderiza cuando *su propio* estado de selección cambia.
- **Drag-drop cross-layer:** Event bus dedicado o extensión del contrato de L2 con un `onExternalDrop` que L2 proxea sin interpretar.
- **Focus management:** Concern transversal fuera de las 3 capas (ver punto 9).

### 8. El schema es un DSL que va a crecer sin control

El schema de traducción ya tiene: `match_rule`, `node_types`, `edge_types`, `render_as`, `color_token`, `visual_encoding`, `target_array`. Cada dominio nuevo necesitará reglas nuevas. No hay:

- **Versionado del schema** — ¿qué pasa cuando la estructura cambia?
- **Validación del schema** — ¿cómo saber si un schema es válido antes de pasarlo a `schemaToGraph()`?
- **Documentación del schema** — cada campo, qué acepta, qué pasa si falta
- **Migración** — schemas viejos con datos existentes

**Recomendación:** JSON Schema para validar los representation schemas. Versión explícita (`"schema_version": "1.0"`). Función `validateSchema()` que corre antes de `schemaToGraph()`.

### 9. Accesibilidad (a11y) y Focus Management no existen como concern

La crítica del punto 7 menciona conflictos de atajos de teclado, pero el problema es más profundo: **navegar un grafo espacial con teclado o lector de pantalla no tiene contrato**.

**El conflicto de foco entre capas:** Cuando el usuario presiona Tab, ¿quién controla el destino? ¿L2 (Canvas) moviendo foco de nodo a nodo? ¿O L3 (editor interno) navegando entre inputs de un formulario JSON? Si un Monaco editor en L3 captura todo el input de teclado (focus trap), el usuario no puede salir al canvas sin saber el atajo mágico.

Esto no es un nice-to-have de accesibilidad — es un **bug de UX** que afecta a todos los usuarios power-user que navegan con teclado.

**Recomendación:** Contrato explícito de delegación de foco con dos modos:

1. **Modo Canvas (L2 owns focus):** Flechas direccionales navegan entre nodos. Tab cicla nodos. L3 renderiza en modo pasivo (preview, no editable).
2. **Modo Edición (L3 owns focus):** `Enter` en un nodo "hunde" el foco hacia L3, delegando control total al editor interno. `Escape` devuelve el foco a L2.

Esto es análogo a cómo funcionan las celdas en Google Sheets (navegar vs editar) y es un patrón probado.

### 10. TypeScript desaparece en runtime — falta validación de datos reales

El punto 1 propone discriminated unions para tipar el payload. Correcto, pero insuficiente: **TypeScript no existe en tiempo de ejecución**. Si la API o Neo4j envía un JSON que dice `contentType: 'markdown'` pero `content` es un número, L3 crashea igual — TypeScript no lo va a prevenir.

Esto es crítico porque el sistema es **multi-dominio**: cada schema nuevo es una fuente nueva de datos malformados, y la frontera L1→L2 es donde entran datos del mundo exterior.

**Recomendación:** Integrar validación en runtime (Zod o Valibot) en la frontera entre el mundo exterior y el AST. Esto se puede hacer en dos puntos:

1. **`schemaToGraph()` valida sus outputs** — cada ASTNode sale validado contra el schema Zod correspondiente a su `contentType`. Si falla, el nodo se marca con un tipo especial `error` en lugar de crashear.
2. **El Node Type Registry valida en el lookup** — cuando L2 le pide al registry el renderer para un `typeId`, el registry valida el payload contra el `payload_schema` registrado antes de retornar el componente.

```typescript
// Ejemplo: el pipeline de traducción con validación
const matched = matchNodes(rawData, schema.node_types);
const topology = resolveTopology(matched, schema.topology);
const ast = resolveEdges(topology, schema.edge_types);
const { valid, errors } = validateAST(ast, payloadSchemas);  // Zod validation
// errors → nodos con type 'error' que renderizan fallback visual
```

Esto emparejado con tipar los `any` es probablemente el **cambio de mayor impacto con menor esfuerzo** — da estabilidad inmediata sin tocar la arquitectura de capas.

### 11. Los eventos semánticos no están preparados para colaboración

El sistema asume un solo usuario. Pero las arquitecturas de grafos (Figma, Miro, FigJam) suelen evolucionar hacia multiplayer, y la estructura de los eventos semánticos definida hoy determina si eso es posible mañana.

El doc `01c_editor_state_and_history_contract.md` define acciones semánticas (create node, edit payload, etc.) pero como **operaciones imperativas** acopladas al estado local, no como **objetos serializables**.

**El costo de no hacer nada:** Si en 6 meses se quiere agregar colaboración, hay que reescribir toda la capa de history + persistence para extraer los eventos en un formato que se pueda transmitir (WebSocket) o reconciliar (CRDTs).

**El costo de hacerlo ahora:** Casi cero — solo requiere que las acciones semánticas sean **objetos planos serializables** en lugar de closures o mutaciones directas:

```typescript
// En lugar de:
setNodes(prev => prev.map(n => n.id === id ? { ...n, data: newData } : n));

// Emitir:
const action: SemanticAction = {
  type: 'PAYLOAD_EDITED',
  nodeId: id,
  prevPayload: oldData,
  nextPayload: newData,
  actor: userId,
  timestamp: Date.now(),
};
dispatch(action); // history lo registra, store lo aplica
```

No se necesita implementar CRDTs ni WebSockets hoy. Solo estructurar las acciones como datos puros (estilo Redux) deja la puerta abierta sin costo adicional.

### 12. El payload se renderiza como HTML — no hay sanitization

El sistema acepta contenido arbitrario en `payload.contentData` y lo pasa a editores que lo renderizan como HTML (markdown → HTML, JSON preview con syntax highlighting, etc.). No hay sanitization en ningún punto del pipeline.

**El vector de ataque:** Un payload con `contentType: 'markdown'` y `content: '![img](x onerror=alert(1))'` o contenido con `<script>` embebido pasa directo de Neo4j/API → `schemaToGraph()` → L2 → L3 → `dangerouslySetInnerHTML` o equivalente en el markdown renderer.

Esto no es un problema hipotético — el sistema está diseñado para renderizar contenido que viene de fuentes externas (job postings scrapeados, datos de API, contenido editado por usuarios).

**Recomendación:** Sanitization en la frontera, no en el renderer. Dos opciones:

1. **En `schemaToGraph()`** — sanitizar todo `contentData` al generar el AST. Ventaja: un solo punto. Desventaja: performance hit en la traducción.
2. **En el Node Type Registry** — cada tipo registra su sanitizer junto con su renderer. Ventaja: sanitization específica por tipo (markdown necesita DOMPurify, JSON no necesita nada, imágenes necesitan validar URLs). Desventaja: fácil de olvidar al registrar un tipo nuevo.

**Opción recomendada:** La 2, pero con un **default deny** — si un tipo no registra sanitizer, el registry lo envuelve en un sanitizer genérico (DOMPurify con config estricta). Esto empareja bien con la validación Zod del punto 10: Zod valida la forma, DOMPurify valida el contenido.

### 13. El Node Type Registry necesita soportar lazy loading

El registry de `01b_node_type_registry_and_modes.md` define renderers por tipo: `minimized`, `focus`, `edit_in_context`, `full_editor`. Pero si todos los renderers se importan estáticamente, el bundle carga Monaco, el markdown renderer, el table editor, y todos los demás al inicio — independientemente de si el grafo actual los necesita.

Esto es una decisión de **contrato del registry**, no solo de build:

```typescript
// Estático — todo en el bundle inicial
renderers: {
  minimized: MinimalCodeView,
  full_editor: MonacoEditor,  // +800KB
}

// Lazy — carga bajo demanda
renderers: {
  minimized: MinimalCodeView,
  full_editor: React.lazy(() => import('./MonacoEditor')),
}
```

Si el registry no está diseñado para aceptar `React.lazy()` componentes desde el día 1, retrofit es doloroso (hay que agregar `<Suspense>` boundaries, fallbacks, y manejar el estado de carga dentro del NodeShell).

**Recomendación:** El contrato del registry debe exigir que `renderers` sea `ComponentType | LazyExoticComponent`, y `NodeShell` debe envolver el render en `<Suspense fallback={<NodeSkeleton />}>` siempre. Costo: ~5 líneas de código ahora. Costo de no hacerlo: refactor de todos los node types cuando el bundle pase el threshold.

### 14. No hay Contract Testing entre capas

El aislamiento L1/L2/L3 es una promesa verbal — no hay nada que la enforcea con el tiempo. Un desarrollador puede agregar un campo al contrato de L2, olvidar actualizar el schema parser de L1, y el sistema compila pero crashea en runtime.

**Recomendación:** Tests que validan exclusivamente que las salidas de una capa son consumibles por la siguiente, sin montar UI:

```typescript
// contract.test.ts
describe('L1 → L2 contract', () => {
  it('schemaToGraph output satisfies AppToCanvasProps', () => {
    const ast = schemaToGraph(sampleRawData, sampleSchema);
    // Zod parse — falla si el contrato cambió sin actualizar el parser
    AppToCanvasPropsSchema.parse({ astNodes: ast.nodes, astEdges: ast.edges });
  });
});

describe('L2 → L3 contract', () => {
  it('every ASTNode.payload is valid for its registered type', () => {
    const ast = schemaToGraph(sampleRawData, sampleSchema);
    for (const node of ast.nodes) {
      const schema = registry.getPayloadSchema(node.typeId);
      schema.parse(node.payload); // Zod — fails if payload shape drifted
    }
  });
});
```

Si Zod ya se adopta para validación runtime (punto 10), estos tests salen casi gratis — reusan los mismos schemas.

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

### Impacto alto, esfuerzo bajo (hacer primero)

1. **Tipar el payload + validación Zod en runtime** — discriminated unions en compile time, Zod en la frontera L1→L2. Da estabilidad inmediata sin cambiar la arquitectura. Los schemas Zod se reusan para contract testing.
2. **Reconciliar el Node Type Registry con los contratos** — el registry es la fuente de verdad para tipos de nodo, no el enum en el contrato. Elimina el acoplamiento L2→L3.
3. **Decidir dagre vs elkjs** una sola vez, actualizar todos los docs. Es una decisión de 10 minutos que desbloquea coherencia en 5 documentos.
4. **Sanitization del payload** — DOMPurify como default deny en el registry. Sin esto, contenido externo (job postings scrapeados) es un vector XSS directo.
5. **Lazy loading en el registry** — `<Suspense>` en NodeShell + renderers como `ComponentType | LazyExoticComponent`. ~5 líneas ahora, evita refactor de todos los node types después.

### Impacto alto, esfuerzo medio (diseñar antes de implementar)

6. **Diseñar la serialización inversa** (`astToDomain`) — sin esto, la edición no puede persistirse. Más difícil que el parsing original.
7. **Definir la frontera de undo** entre L3 (local/keystroke) y L2 (semántico/action). Documentar que `onContentMutate` es el punto de transición.
8. **Contrato de delegación de foco** — modo Canvas (L2 owns) vs modo Edición (L3 owns), con Enter/Escape como transición. Afecta a todos los usuarios de teclado.
9. **Modelo de error** en los contratos y en `schemaToGraph()` — nodos `error` con fallback visual, no crashes silenciosos.

### Impacto medio, esfuerzo bajo (inversión de futuro casi gratis)

10. **Eventos semánticos como objetos serializables** — estructurar las acciones de history como datos puros (no closures). Prepara colaboración sin costo adicional hoy.
11. **Contract tests entre capas** — si Zod ya está adoptado, estos tests salen casi gratis. Previenen drift silencioso entre L1→L2→L3.

### Documentar y decidir

12. **Escape hatches del aislamiento** — Zustand con selectores atómicos (no Context), event bus para drag-drop, focus management como concern transversal.
13. **Versionado y validación del schema DSL** — `schema_version`, `validateSchema()`, JSON Schema para los representation schemas.

---

## Fuera de alcance de este documento

Los siguientes temas son válidos pero pertenecen a documentos separados — son decisiones de **implementación y operación**, no de arquitectura de capas. Se listan aquí para que no se pierdan:

| Tema | Doc sugerido | Razón |
|------|-------------|-------|
| Virtualización del canvas con 1000+ nodos | Extensión de `02_L2_graph_viewer/graph_foundations.md` | Es una decisión de implementación de L2, no un problema de contrato entre capas |
| Testing strategy (e2e vs unit vs Storybook) | Nuevo: `_meta/testing_strategy.md` | Tooling y proceso, no arquitectura |
| Mock API → L1 y caching (React Query) | Extensión de `01_L1_ui_app/schema_integration.md` | Es implementación de la capa de datos de L1 |
| Estructura de archivos en `src/` | Nuevo: `_meta/project_structure.md` | Organización física, no conceptual |
| Bundle splitting | Nuevo: `_meta/project_structure.md` | Build concern — aunque lazy loading del registry (punto 13 arriba) lo habilita |
| Migración desde código legacy | Nuevo: `_meta/migration_plan.md` | Plan de ejecución, no análisis de diseño |
| Logging y observabilidad | Nuevo: `_meta/observability.md` | Concern operacional transversal |
