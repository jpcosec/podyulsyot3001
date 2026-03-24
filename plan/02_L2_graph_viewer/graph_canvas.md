# L2: Graph Canvas

> Motor espacial. Renderiza ReactFlow, maneja layout, topología. No conoce el dominio.

---

## Componentes

| Componente | Descripción |
|------------|-------------|
| `UniversalGraphCanvas` | Wrapper principal de ReactFlow |
| `UniversalNodeShell` | Cascarón visual para nodos |
| `UniversalGroupShell` | Cascarón para grupos colapsables |
| `ProxyEdge` | Edge custom para conexiones cruzadas |
| `LayoutEngine` | Dagre/ELK para auto-layout |

---

## Responsabilidades

- **Renderizar ReactFlow** - Nodes, edges, controls, minimap
- **Calcular posiciones** - Layout engine (Dagre/ELK)
- **Gestionar selección** - Click, multi-select
- **Subflows** - Grupos anidados, collapse/expand
- **Eventos hacia arriba** - onNodeClick, onTopologyMutate
- **NO conoce dominio** - Solo recibe AST, no sabe qué es un "Job" o "CV"

---

## Contrato L1 → L2

```typescript
// L1 le pasa:
interface L1ToL2Props {
  nodes: ASTNode[];      // AST completo
  edges: ASTEdge[];
  themeTokens: Record<string, StyleToken>;
  isReadOnly?: boolean;
}
```

```typescript
// L2 emite hacia L1:
interface L2ToL1Events {
  onNodeClick: (nodeId: string, attributes: Record<string, any>) => void;
  onEdgeClick: (edgeId: string) => void;
  onSelectionChange: (nodes: string[], edges: string[]) => void;
  onTopologyMutate: (newAST: AST) => void;
}
```

---

## Contrato L2 → L3

```typescript
// L2 le pasa a cada nodo:
interface L2ToL3Props {
  nodeId: string;
  isFocused: boolean;
  payload: NodePayload;           // { contentType, contentData }
  visualToken: string;            // Para estilos
}
```

```typescript
// L3 emite hacia L2:
interface L3ToL2Events {
  onContentMutate: (nodeId: string, newPayload: any) => void;
  onRequestFocus: (nodeId: string) => void;
}
```

---

## Estructura de UniversalNodeShell

```tsx
export function UniversalNodeShell({ data }) {
  const { astNode, themeTokens, onNodeClick } = data;
  const style = themeTokens[astNode.visualToken];

  return (
    <div style={{ borderColor: style.border, background: style.bg }}>
      <Handle type="target" />
      <div className="node-header">{astNode.payload.title}</div>
      <InternalNodeRouter payload={astNode.payload} />
      <Handle type="source" />
    </div>
  );
}
```

**Clave:** `InternalNodeRouter` es L3 - L2 solo lo importa y lo renderiza.

---

## Dependencias Externas

- `@xyflow/react` - ReactFlow
- `dagre` / `elkjs` - Layout engine
- Foundation atoms - Button, Badge, Icon (para toolbar)
