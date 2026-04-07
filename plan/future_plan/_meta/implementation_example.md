# Implementación: Los 3 Niveles en Código

> Ejemplo concreto de cómo implementar la arquitectura de 3 capas en React, siguiendo los contratos definidos.

---

## 0. El Contrato (Types)

```typescript
// types/ast.types.ts
export interface ASTNode {
  id: string;
  parentId?: string;
  visualToken: string;
  isSubflow: boolean;
  payload: {
    title: string;
    contentType: 'markdown' | 'tags' | 'json' | 'empty';
    contentData: any;
  };
  attributes: Record<string, any>;
}

export interface ASTEdge {
  id: string;
  source: string;
  target: string;
  visualToken: string;
  label?: string;
}
```

---

## Nivel 1: App (El Orquestador)

```typescript
// features/job-pipeline/pages/MatchPage.tsx
import { schemaToGraph } from '../lib/schemaToGraph';
import { UniversalGraphCanvas } from '../../../components/organisms/UniversalGraphCanvas';
import { MatchControlPanel } from '../components/MatchControlPanel';
import matchSchema from '../schemas/match.schema.json';

export function MatchPage({ jobId }) {
  // 1. Fetching
  const { data: rawData } = useQuery(['job', jobId], fetchJobData);
  
  // 2. Parseo a AST
  const { astNodes, astEdges } = useMemo(() => {
    if (!rawData) return { astNodes: [], astEdges: [] };
    return schemaToGraph(rawData, matchSchema);
  }, [rawData]);

  // 3. Layout
  return (
    <div className="flex h-screen">
      <aside className="w-80">
        <MatchControlPanel />
      </aside>
      <main className="flex-1">
        <UniversalGraphCanvas 
          nodes={astNodes} 
          edges={astEdges}
          themeTokens={matchSchema.visual_encoding.color_tokens}
        />
      </main>
    </div>
  );
}
```

**Responsabilidades:**
- Fetching de datos
- Parseo a AST via `schemaToGraph`
- Layout de la App (Sidebar + Canvas)
- No sabe qué es React Flow

---

## Nivel 2: Graph Canvas (El Motor Espacial)

```typescript
// components/organisms/UniversalGraphCanvas.tsx
import { ReactFlow, useNodesState } from '@xyflow/react';
import { NodeShell } from './NodeShell';

const nodeTypes = { universal: NodeShell };

export function UniversalGraphCanvas({ nodes, edges, themeTokens, onNodeClick }) {
  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState(
    nodes.map(astNode => ({
      id: astNode.id,
      type: 'universal',
      parentId: astNode.parentId,
      data: { astNode, themeTokens, onNodeClick },
      position: { x: 0, y: 0 }
    }))
  );

  return (
    <ReactFlow 
      nodes={flowNodes}
      edges={edges}
      nodeTypes={nodeTypes}
    >
      <Background />
      <Controls />
    </ReactFlow>
  );
}

// NodeShell.tsx - El cascarón
export function NodeShell({ data }) {
  const { astNode, themeTokens } = data;
  const style = themeTokens[astNode.visualToken];

  return (
    <div 
      style={{ borderColor: style.border, backgroundColor: style.bg }}
      className="rounded-lg border-2 p-4"
    >
      <Handle type="target" position={Position.Top} />
      <h3>{astNode.payload.title}</h3>
      <InternalNodeRouter payload={astNode.payload} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
```

**Responsabilidades:**
- Renderizar React Flow
- Manejar posiciones X/Y
- Dibujar cascarones de nodos
- No sabe qué es "Job" o "CV"

---

## Nivel 3: Internal Node (La Carne)

```typescript
// components/organisms/InternalNodeRouter.tsx
import { IntelligentEditor } from './IntelligentEditor';
import { JsonPreview } from '../molecules/JsonPreview';

export function InternalNodeRouter({ payload }) {
  switch (payload.contentType) {
    case 'tags':
      return (
        <IntelligentEditor 
          content={payload.contentData} 
          mode="tag-hover"
        />
      );
    case 'json':
      return <JsonPreview data={payload.contentData} />;
    case 'empty':
    default:
      return null;
  }
}
```

**Responsabilidades:**
- Renderizar contenido interactivo
- No sabe que vive en un grafo
- Funcionaría igual en una tabla o modal

---

## Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│ L1: MatchPage                                              │
│   1. fetchJobData() → rawData                             │
│   2. schemaToGraph(rawData) → AST                         │
│   3. <UniversalGraphCanvas nodes={AST} />                 │
└─────────────────────────┬───────────────────────────────────┘
                          │ AST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ L2: UniversalGraphCanvas                                   │
│   1. Map AST → flowNodes                                   │
│   2. ReactFlow.render()                                    │
│   3. <NodeShell data={astNode} />                          │
└─────────────────────────┬───────────────────────────────────┘
                          │ astNode.payload
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ L3: InternalNodeRouter                                     │
│   payload.contentType === 'tags'                           │
│   → <IntelligentEditor />                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Docs Relacionados

- `_meta/06_flow_contract.md` - Contratos completos
- `ARCHITECTURE.md` - Modelo de 3 capas
