# Propuesta: Separación del Monolito KnowledgeGraph.tsx

## Estado Actual

```
src/pages/global/KnowledgeGraph.tsx  (~3000 líneas)
├── L1: Page logic (state, filters, sidebar)
├── L2: ReactFlow rendering
└── L3: Internal components (inline)
```

## Estructura Objetivo

```
src/
├── features/
│   └── node-editor/
│       ├── pages/
│       │   └── NodeEditorPage.tsx        # L1: Orquestación
│       │
│       ├── components/
│       │   ├── canvas/
│       │   │   ├── UniversalGraphCanvas.tsx   # L2
│       │   │   ├── UniversalNodeShell.tsx     # L2
│       │   │   └── UniversalGroupShell.tsx    # L2
│       │   │
│       │   └── content/
│       │       ├── InternalNodeRouter.tsx     # L3
│       │       ├── IntelligentEditor.tsx       # L3
│       │       └── JsonPreview.tsx             # L3
│       │
│       └── lib/
│           └── schemaToGraph.ts           # L1: Traducción
```

## Plan de Migración (Step-by-Step)

### Fase 1: Extraer L3 (Contenido)
1. Crear `features/node-editor/components/content/`
2. Mover componentes inline de KnowledgeGraph a content/
3. Crear `InternalNodeRouter.tsx`
4. **Validar:** Editor sigue funcionando dentro del grafo

### Fase 2: Extraer L2 (Canvas)
1. Crear `features/node-editor/components/canvas/`
2. Mover lógica de ReactFlow a `UniversalGraphCanvas.tsx`
3. Extraer `UniversalNodeShell.tsx`, `UniversalGroupShell.tsx`
4. **Validar:** Canvas renderiza nodos correctamente

### Fase 3: Extraer L1 (Page)
1. Crear `features/node-editor/pages/NodeEditorPage.tsx`
2. Mover sidebar, filtros, state management
3. Crear `NodeInspectorSidebar.tsx`
4. **Validar:** Página completa funciona igual

### Fase 4: Limpieza
1. Eliminar KnowledgeGraph.tsx
2. Actualizar routing en App.tsx
3. Eliminar código duplicado

## Contracts a Definir

```typescript
// features/node-editor/types/contracts.ts

// L1 → L2
export interface AppToCanvasProps {
  nodes: ASTNode[];
  edges: ASTEdge[];
  themeTokens: Record<string, StyleToken>;
  isReadOnly: boolean;
}

export interface CanvasToAppEvents {
  onNodeClick: (nodeId: string, attributes: Record<string, any>) => void;
  onTopologyMutate: (newAST: AST) => void;
}

// L2 → L3
export interface CanvasToNodeProps {
  nodeId: string;
  isFocused: boolean;
  payload: NodePayload;
}

export interface NodeToCanvasEvents {
  onContentMutate: (nodeId: string, newPayload: any) => void;
}
```

## Dependencias After

```
NodeEditorPage (L1)
    ↓ props
UniversalGraphCanvas (L2)
    ↓ data
UniversalNodeShell (L2)
    ↓ payload
InternalNodeRouter (L3)
    ↓
IntelligentEditor / JsonPreview (L3)
```

## Notas

- Mantener KnowledgeGraph.tsx hasta que todo迁移 esté validado
- Usar feature flags para switch entre old/new
- Tests e2e como validación principal
