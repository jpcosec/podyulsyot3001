# Análisis de Proyectos Similares - Node Graph Editors

**Fecha:** 2026-03-26

---

## Propósito

Documentar cómo otros proyectos similares implementan sus editores de grafos basados en nodos para informar decisiones arquitectónicas.

---

## 1. FlowiseAI/Flowise

**Repo:** https://github.com/FlowiseAI/Flowise
**Stack:** ReactFlow + React + Zustand + TypeScript

### Representación de Nodos

Flowise tiene **100+ tipos de nodos custom** pero usa un patrón simple:

```typescript
// Definición de tipo de nodo
type ChatOpenAINode = Node<{
  label: string;
  modelName: string;
  temperature: number;
  maxTokens: number;
}, 'chatOpenAI'>;

// nodeTypes registry
const nodeTypes = {
  chatOpenAI: ChatOpenBINode,
  // ... 100+ más
};

// Uso en ReactFlow
<ReactFlow nodeTypes={nodeTypes} nodes={nodes} edges={edges} />
```

### data del nodo

La información se guarda **directamente en `data`** del nodo ReactFlow:

```typescript
const node = {
  id: '1',
  type: 'chatOpenAI',
  position: { x: 0, y: 0 },
  data: {
    label: 'GPT-4',
    modelName: 'gpt-4',
    temperature: 0.7,
    // ... todas las propiedades
  }
};
```

### Interfaz con ReactFlow

- **NO usan capas intermedias** entre ReactFlow y sus datos
- El `data` del nodo **ES** su configuración
- No hay "AST" o traducción - usan los datos directamente

### Parent/Child

- Usan ReactFlow nativo `parentId` + `extent: 'parent'`
- Los nodos grupo tienen `type: 'group'`

### Separación de Capas (Layers)

- **NO** tienen separación tipo "L1/L2/L3"
- Todo está en el componente ReactFlow directamente
- Los paneles (sidebar, inspector) son componentes hermanos

### Código Genérico

```typescript
// Cada nodo es un componente simple que lee su data
function ChatOpenBINode({ data }: NodeProps) {
  return (
    <div>
      <label>{data.label}</label>
      <select value={data.modelName}>
        <option value="gpt-4">GPT-4</option>
      </select>
    </div>
  );
}
```

---

## 2. altenull/json-sea

**Repo:** https://github.com/altenull/json-sea
**Stack:** ReactFlow + Next.js + Zustand + dagre

### Representación de Nodos

Visualiza JSON como grafo. Tipos de nodos limitados:

```typescript
// node types son types de ReactFlow, NO tipos de datos
const nodeTypes = {
  array: ArrayNode,
  object: ObjectNode,
  primitive: PrimitiveNode,
};

// El tipo de nodo ReactFlow representa el TIPO DE DATO JSON
const node = {
  id: 'items',
  type: 'array',  // <-- tipo ReactFlow (ArrayNode component)
  data: {
    arrayIndex: 0,
    items: [...],
    isRootNode: false
  }
};
```

### data del nodo

- `data` contiene la información del JSON (índice, items, valores)
- **NO hay separación** entre "schema" y "data"
- El JSON se parsea y cada valor se convierte en nodo

### Layout

- Usa **dagre** para layout (ya instalado)
- Layout hierarchical con workers para archivos grandes
- `rankdir: 'LR'` (izquierda a derecha)

```typescript
// De json-sea/src/store/json-engine/helpers/sea-node-position.helper.ts
import dagre from 'dagre';

function getLayoutedElements(nodes, edges) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'LR', nodesep: 50, ranksep: 100 });
  
  nodes.forEach(node => {
    g.setNode(node.id, { width: 200, height: 100 });
  });
  
  edges.forEach(edge => {
    g.setEdge(edge.source, edge.target);
  });
  
  dagre.layout(g);
  
  return nodes.map(node => ({
    ...node,
    position: {
      x: g.node(node.id).x - 100,
      y: g.node(node.id).y - 50
    }
  }));
}
```

### Separación de Capas

- **L1 (Page):** `page.tsx` (Next.js)
- **L2 (Canvas):** `JsonDiagram.tsx` (ReactFlow wrapper)
- **L3 (Content):** `ArrayNode.tsx`, `ObjectNode.tsx`, `PrimitiveNode.tsx`
- **Stores:** Zustand separado por dominio (`json-engine.store.ts`, `node-detail-view.store.ts`)

### Inspector/Paneles

- Panel derecho muestra detalles del nodo seleccionado
- Cada tipo de nodo tiene su propio "detail component"

---

## 3. dustland/agentok

**Repo:** https://github.com/dustland/agentok
**Stack:** ReactFlow + Next.js + custom state

### Representación de Nodos

Nodos para agentes AI (Assistant, User, WebSurfer, etc.):

```typescript
// nodeTypes simple
const nodeTypes = {
  assistant: AssistantNode,
  user: UserNode,
  websurfer: WebSurferNode,
  conversableAgent: ConversableAgentNode,
  // etc
};
```

### data del nodo

- `data` contiene configuración del agente/LLM
- Ejemplo:
```typescript
const node = {
  id: 'assistant-1',
  type: 'assistant',
  data: {
    name: 'Assistant',
    model: 'gpt-4',
    apiKey: '...', // credential
    systemMessage: 'You are a helpful assistant.',
  }
};
```

### Interfaz con ReactFlow

- Similar a Flowise - **sin capa intermedia**
- Los nodos tienen su propia UI (Forms para configurar cada tipo)

### Parent/Child

- NO usan grupos/containers
- Usan edges para representar conversación entre agentes
- No hay nesting de nodos

### Separación de Capas

- **L1:** Next.js pages (`app/`)
- **L2:** Componentes de Flow (`flow-canvas.tsx`, `flow-editor.tsx`)
- **L3:** Nodos custom (`node/assistant.tsx`, `node/user.tsx`)
- **Store:** Zustand (`store/chats.ts`, `store/projects.ts`)

### Característica Distintiva

- **Genera código Python** a partir del grafo visual
- El grafo es una representación intermedia para generar código AG2

---

## Síntesis Comparativa

| Aspecto | Flowise | json-sea | agentok |
|---------|---------|----------|---------|
| **Framework** | ReactFlow | ReactFlow | ReactFlow |
| **nodeTypes** | 100+ custom | 3 types | ~8 types |
| **data del nodo** | Directo en `data` | Parseado de JSON | Directo en `data` |
| **Layout** | ? | dagre (LR) | ? |
| **Parent/Child** | ReactFlow native | ReactFlow native | No usa |
| **Capas L1/L2/L3** | No | Sí | No |
| **Store** | Zustand | Zustand | Zustand |
| **Generación código** | No | No | Sí (Python) |

---

## Patrones Comunes

### 1. data = configuración directa

Todos los proyectos (excepto json-sea que transforma JSON) usan `node.data` directamente como la configuración del nodo. **No hay traducción a un "AST" intermediario.**

### 2. nodeTypes simple registry

```typescript
const nodeTypes = {
  [tipo1]: Componente1,
  [tipo2]: Componente2,
};
```

### 3. Sin capa de traducción

Flowise y agentok pasan los datos **directamente** a ReactFlow. No hay `schemaToGraph`, ni `asCanvasNode`, ni transformaciones intermedias.

### 4. Componente = renderer + form

Cada nodo custom es simultáneamente:
- Renderer visual (qué se ve en el canvas)
- Form de configuración (qué propiedades tiene)

### 5. Separación UI/Store

Los 3 usan Zustand para estado, pero la UI no tiene capas intermedias complicadas.

---

## Conclusiones para Nuestro Proyecto

### Lo que deberíamos hacer:

1. **Eliminar `schemaToGraph` y capas de traducción**
   - Dejar que el JSON venga en formato ReactFlow nativo
   - O si hay transformación, que sea mínima y en el borde (data provider)

2. **Simplificar `data` del nodo**
   - No crear estructura `{ typeId, payload, properties }`
   - Usar directamente lo que viene en el JSON

3. **nodeTypes directo**
   - Definir los tipos de nodos que necesitamos
   - No crear registry genérico que luego hay que mapear

4. **Seguir el patrón de json-sea para grupos**
   - Usar `type: 'group'` de ReactFlow
   - Con `extent: 'parent'` para hijos

5. **dagre para layout** (ya implementado)

### Lo que NO deberíamos hacer:

- ❌ Crear un "AST" intermediario que no existe en ningún otro proyecto
- ❌ Mantener registro de tipos separado que hay que mapear
- ❌ Capas de traducción complejas (schema → graph → canvas)

### Estructura sugerida:

```
data-provider.ts     → Carga datos (puede transformar si es necesario)
  ↓
graph-data.json      → Datos en formato ReactFlow nativo
  ↓
GraphCanvas.tsx      → Pasa nodeTypes y nodes directamente a ReactFlow
  ↓
nodeTypes = {        → Registry simple de componentes
  group: GroupNode,
  default: DefaultNode,
}
```

---

## Recomendación Final

**Seguir el camino de Flowise/agentok** - datos simples en `data`, sin capas intermedias, nodeTypes registry simple.

El JSON de prueba debería venir directamente en formato ReactFlow:

```json
{
  "nodes": [
    { "id": "1", "type": "group", "data": { "label": "Vehículos" }, "position": {...} },
    { "id": "2", "type": "default", "data": { "label": "Autos", "category": "entry" }, "parentId": "1", "extent": "parent" }
  ]
}
```

Y eliminar todo el código de traducción que no está en ninguno de estos 3 proyectos.
