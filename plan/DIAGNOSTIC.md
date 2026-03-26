# Diagnóstico de Problemas - Node Editor

**Fecha:** 2026-03-26
**Estado:** Problemas identificados en runtime - Análisis de proyectos similares completado

---

## Problema 1: Worker ELK no funciona en browser

**Síntoma:**
```
TypeError: _Worker is not a constructor
    at ELKNode2.optionsClone.workerFactory
```

**Causa raíz:**
- El código usa `new Worker(new URL('./elk.worker.ts', import.meta.url))` para crear un Web Worker
- El bundler (Vite) no soporta correctamente workers inline con ELK en este setup
- El worker intenta importar `elkjs/lib/elk.bundled.js` pero falla en el browser

**Solución aplicada:**
- Se cambió `use-graph-layout.ts` para ejecutar ELK en el thread principal (síncrono)
- Esto resuelve el error pero pierde el beneficio de worker thread

**Recomendación a largo plazo:**
- Volver a `dagre` o `dagre-d3` para layout (más simple, sin worker)
- O usar ReactFlow built-in `useReactFlow().fitView()` para positioning básico
- Eliminar el worker code completamente

---

## Problema 2: "It looks like you have created a new nodeTypes or edgeTypes object"

**Síntoma:**
- Warning de ReactFlow en consola
- Nodos renderizando como "Unknown node type"

**Causa raíz:**
- Los datos del grafo usan `type: "group"` y `type: "simple"`
- El registry solo tenía tipos: `person`, `skill`, `project`, etc.
- Faltaban los tipos `group` y `simple` en `register-defaults.ts`

**Solución aplicada:**
- Agregados tipos `group` y `simple` al registry

---

## Problema 3: Nodos no renderizan correctamente (quedan como "Unknown")

**Síntoma visible:**
- Se ven las aristas correctamente
- Los nodos aparecen como "Unknown: error" con mensaje "Unknown node type: group/simple"

**Causa raíz:**
- El tipo en el dato JSON (`type: "group"`) no coincide con ningún tipo registrado
- El renderer para esos tipos no está siendo usado

---

## Recomendaciones para reducir custom code

### 1. Usar ReactFlow nativo para nodos/edges

En vez de definir `nodeTypes` custom, usar:
```ts
// En lugar de custom NodeShell
import { Handle, Position } from 'reactflow';

// Nodo simple que usa API nativa
function SimpleNode({ data }) {
  return (
    <div className="node">
      <Handle type="target" position={Position.Top} />
      {data.name}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
```

### 2. Usar dagre para layout (sin worker)

```ts
import dagre from 'dagre';
import { useNodesState, useEdgesState } from 'reactflow';

function getLayoutedElements(nodes, edges) {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: 'LR' });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: node.width, height: node.height });
  });
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: { x: nodeWithPosition.x - 100, y: nodeWithPosition.y - 30 },
    };
  });
}
```

### 3. Usar parent/child nativo de ReactFlow

```ts
// En lugar de manejar parentId manualmente
<Node
  id="parent"
  type="group"
  data={{ label: "Parent" }}
  style={{ width: 500, height: 300 }}
>
  <Node id="child" type="default" parentId="parent" extent="parent" />
</Node>
```

---

## Acción inmediata recomendada

1. **Quitar el worker** - ya está corregido para correr en main thread
2. **Simplificar nodeTypes** - usar solo `default` de ReactFlow para nodos simples
3. **Usar dagre** - instalar `dagre` y reemplazar ELK completamente
4. **Limpiar register-defaults.ts** - dejar solo lo mínimo necesario

---

## Tags para seguimiento

- `TODO: replace-elk-with-dagre`
- `TODO: simplify-node-types`
- `TODO: remove-unused-worker-code`
