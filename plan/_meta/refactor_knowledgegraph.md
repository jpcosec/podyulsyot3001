# Refactorización: De KnowledgeGraph a 3 Capas

> Cómo transformar el actual `KnowledgeGraph.tsx` en la arquitectura de 3 capas.

---

## El Problema Actual

`KnowledgeGraph.tsx` tiene ~3000 líneas con:
- Sidebar metida a la fuerza
- Inputs, modales, filtros
- Lógica de negocio mezclada con React Flow

---

## La Solución: 3 Archivos en Lugar de 1

### L1: NodeEditorPage.tsx (Orquestador)

```typescript
import { UniversalGraphCanvas } from '../../../components/organisms/UniversalGraphCanvas';
import { NodeInspectorSidebar } from '../components/NodeInspectorSidebar';
import { schemaToGraph } from '../lib/schemaToGraph';

export function NodeEditorPage() {
  const { data: rawData } = useQuery({ queryKey: ['graph_data'], queryFn: fetchGraph });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [filters, setFilters] = useState({ text: '' });

  // Traducción AST (antes estaba en KnowledgeGraph)
  const { astNodes, astEdges } = useMemo(() => {
    return schemaToGraph(rawData, schema, filters);
  }, [rawData, filters]);

  return (
    <div className="flex h-screen">
      <aside className="w-[320px]">
        <input onChange={e => setFilters(f => ({ ...f, text: e.target.value }))} />
        <NodeInspectorSidebar nodeId={selectedNodeId} />
      </aside>
      <main className="flex-1">
        <UniversalGraphCanvas 
          initialNodes={astNodes}
          initialEdges={astEdges}
          onNodeClick={(id) => setSelectedNodeId(id)}
        />
      </main>
    </div>
  );
}
```

### L2: UniversalGraphCanvas.tsx (Motor Espacial)

```typescript
import { ReactFlow, useNodesState } from '@xyflow/react';
import { UniversalNodeShell } from './UniversalNodeShell';
import { useGraphHistory } from '../../../hooks/useGraphHistory';

const nodeTypes = { node: UniversalNodeShell, group: UniversalGroupShell };

export function UniversalGraphCanvas({ initialNodes, initialEdges, onNodeClick }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const history = useGraphHistory(setNodes, setEdges);

  return (
    <div>
      <div className="absolute top-4 right-4 z-10">
        <button onClick={history.undo}>Undo</button>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, n) => onNodeClick(n.id)}
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
```

### L3: InternalNodeRouter.tsx (Contenido)

```typescript
import { IntelligentEditor } from './IntelligentEditor';
import { JsonPreview } from '../molecules/JsonPreview';

export function InternalNodeRouter({ payload, nodeId }) {
  if (payload.contentType === 'tag_editor') {
    return <IntelligentEditor onChange={(text) => emitMutate(nodeId, text)} />;
  }
  if (payload.contentType === 'json_preview') {
    return <JsonPreview data={payload.contentData} />;
  }
  return null;
}
```

---

## Beneficios de la Separación

| Antes | Después |
|-------|---------|
| 1 archivo de 3000 líneas | 3 archivos de ~100 líneas |
| Sidebar dentro del canvas | Sidebar como componente L1 |
| Filtros mezclados con React Flow | Filtros modifican AST antes del canvas |
| Lógica de negocio en componente visual | Solo props fluyen entre capas |

---

## Migración Paso a Paso

1. **Extraer sidebar** → `NodeInspectorSidebar.tsx` (L1)
2. **Crear página** → `NodeEditorPage.tsx` (L1)
3. **Limpiar KnowledgeGraph** → Solo renderiza ReactFlow (L2)
4. **Separar NodeShell** → Componente puro (L2)
5. **Crear Router** → `InternalNodeRouter.tsx` (L3)

---

## Docs Relacionados

- `ARCHITECTURE.md` - Modelo de 3 capas
- `_meta/implementation_example.md` - Ejemplo genérico
- `L1_ui_app/schema_translation.md` - Motor de traducción
