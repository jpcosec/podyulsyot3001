# Step 6: Custom Edges (FloatingEdge, ButtonEdge)

**Spec:** SPEC_GRP_001  
**Phase:** 3 (UI Components)  
**Priority:** MEDIUM — Required for edgeTypes in GraphCanvas  
**Dependency:** GRP-001-05 (GraphCanvas references these)

---

## 1. Migration Notes

> Not applicable — custom edges are new L2 components. No legacy component to extract.

**Why this step exists:**
- Blueprint: "edges/FloatingEdge.tsx — Bezier edge with intersection"
- Current KnowledgeGraph.tsx has FloatingEdge (lines 748-767) and SubFlowEdge (lines 769-794)
- This step extracts and improves: FloatingEdge with node intersection, ButtonEdge with delete button
- Per Guide: "Edge Inheritance (no ProxyEdge) — edges se reasignan visualmente al colapsar"

---

## 2. Data Contract

### Input: From ReactFlow

```ts
interface EdgeProps {
  id: string;
  source: string;
  target: string;
  sourceHandle: string | null;
  targetHandle: string | null;
  data?: {
    relationType: string;
    properties: Record<string, string>;
    _originalSource?: string;  // For edge inheritance
    _originalTarget?: string;
    onDelete?: (edgeId: string) => void;
  };
  style?: React.CSSProperties;
  markerEnd?: any;
  selected?: boolean;
}
```

### Output: SVG Path

```ts
// Bezier path string from getBezierPath()
type Path = string;

// Edge styling
interface EdgeStyle {
  stroke: string;
  strokeWidth: number;
  strokeDasharray?: string;  // For inherited edges
  opacity?: number;
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/L2-canvas/edges/
│   ├── FloatingEdge.tsx      # Bezier edge with node intersection
│   ├── ButtonEdge.tsx       # Edge with delete button on hover
│   ├── edge-helpers.ts     # Shared calculation utilities
│   └── index.ts            # Export barrel
```

---

## 4. Implementation

### features/graph-editor/L2-canvas/edges/edge-helpers.ts

```ts
import type { Node, Edge } from '@xyflow/react';

/**
 * Calculate intersection point between two nodes
 * Uses node center + half dimensions
 */
export function getNodeIntersection(source: Node, target: Node): { x: number; y: number } {
  const sourceWidth = source.measured?.width ?? 170;
  const sourceHeight = source.measured?.height ?? 68;
  const targetWidth = target.measured?.width ?? 170;
  const targetHeight = target.measured?.height ?? 68;
  
  const sx = source.positionAbsolute.x + sourceWidth / 2;
  const sy = source.positionAbsolute.y + sourceHeight / 2;
  const tx = target.positionAbsolute.x + targetWidth / 2;
  const ty = target.positionAbsolute.y + targetHeight / 2;
  
  // Calculate direction
  const dx = tx - sx;
  const dy = ty - sy;
  
  // Simple intersection at node boundaries
  return {
    x: sx + (dx > 0 ? sourceWidth / 2 : -sourceWidth / 2),
    y: sy + (dy > 0 ? sourceHeight / 2 : -sourceHeight / 2),
  };
}

/**
 * Get edge connection parameters
 */
export interface EdgeParams {
  sx: number;
  sy: number;
  tx: number;
  ty: number;
  sourcePosition: 'top' | 'right' | 'bottom' | 'left';
  targetPosition: 'top' | 'right' | 'bottom' | 'left';
}

export function getEdgeParams(source: Node, target: Node): EdgeParams {
  const sourceIntersection = getNodeIntersection(source, target);
  const targetIntersection = getNodeIntersection(target, source);
  
  // Determine positions based on relative locations
  const sourcePos: 'top' | 'right' | 'bottom' | 'left' = 
    sourceIntersection.y < targetIntersection.y ? 'top' : 'bottom';
  const targetPos: 'top' | 'right' | 'bottom' | 'left' =
    targetIntersection.y < sourceIntersection.y ? 'top' : 'bottom';
  
  return {
    sx: sourceIntersection.x,
    sy: sourceIntersection.y,
    tx: targetIntersection.x,
    ty: targetIntersection.y,
    sourcePosition: sourcePos,
    targetPosition: targetPos,
  };
}

/**
 * Validate connection using registry
 */
export function isValidConnection(
  connection: { source: string; target: string; sourceHandle?: string | null; targetHandle?: string | null },
  registry: { canConnect: (source: string, target: string) => boolean }
): boolean {
  // If handles specify type, validate
  if (connection.sourceHandle && connection.targetHandle) {
    return registry.canConnect(connection.sourceHandle, connection.targetHandle);
  }
  // Otherwise allow (type validation happens on edge creation)
  return true;
}
```

### features/graph-editor/L2-canvas/edges/FloatingEdge.tsx

```tsx
import { memo } from 'react';
import { 
  BaseEdge, 
  getBezierPath, 
  useStore, 
  type EdgeProps,
} from '@xyflow/react';
import { getEdgeParams } from './edge-helpers';

export const FloatingEdge = memo(function FloatingEdge({
  id,
  source,
  target,
  style,
  markerEnd,
  data,
}: EdgeProps) {
  const sourceNode = useStore((s) => s.nodeLookup.get(source));
  const targetNode = useStore((s) => s.nodeLookup.get(target));
  
  // Don't render if nodes not found
  if (!sourceNode || !targetNode) return null;
  
  const params = getEdgeParams(sourceNode, targetNode);
  const [path] = getBezierPath({
    sourceX: params.sx,
    sourceY: params.sy,
    sourcePosition: params.sourcePosition,
    targetX: params.tx,
    targetY: params.ty,
    targetPosition: params.targetPosition,
  });
  
  // Inherited edge styling (from group collapse)
  const isInherited = data?.relationType === 'inherited';
  const edgeStyle = isInherited
    ? {
        ...style,
        strokeDasharray: '3 4',
        opacity: 0.5,
        stroke: 'rgba(116, 117, 120, 0.7)',
      }
    : style;
  
  return (
    <BaseEdge
      id={id}
      path={path}
      style={edgeStyle}
      markerEnd={isInherited ? undefined : markerEnd}
    />
  );
});
```

### features/graph-editor/L2-canvas/edges/ButtonEdge.tsx

```tsx
import { memo, useState, useCallback } from 'react';
import { EdgeLabelRenderer, type EdgeProps } from '@xyflow/react';
import { FloatingEdge } from './FloatingEdge';
import { useGraphStore } from '@/stores/graph-store';

export const ButtonEdge = memo(function ButtonEdge(props: EdgeProps) {
  const [showButton, setShowButton] = useState(false);
  const removeElements = useGraphStore(s => s.removeElements);
  
  const handleDelete = useCallback(() => {
    removeElements([], [props.id]);
  }, [props.id, removeElements]);
  
  return (
    <>
      <FloatingEdge {...props} />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: 'translate(-50%, -50%)',
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
          onMouseEnter={() => setShowButton(true)}
          onMouseLeave={() => setShowButton(false)}
        >
          <button
            onClick={handleDelete}
            className={`
              w-5 h-5 flex items-center justify-center
              bg-white border border-border rounded
              text-xs text-muted-foreground
              hover:bg-destructive hover:text-destructive-foreground hover:border-destructive
              transition-colors
              ${showButton ? 'block' : 'hidden'}
            `}
          >
            ×
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  );
});
```

### features/graph-editor/L2-canvas/edges/index.ts

```ts
export { FloatingEdge } from './FloatingEdge';
export { ButtonEdge } from './ButtonEdge';
export { getNodeIntersection, getEdgeParams, isValidConnection } from './edge-helpers';
```

---

## 5. Styles (Terran Command)

- Default edge: `stroke: #334155`, `strokeWidth: 1.5`
- Inherited edge: `strokeDasharray: 3 4`, `opacity: 0.5`
- Per Guide: defined in xy-theme.css (step 11)

---

## 6. Definition of Done

```
[ ] FloatingEdge renders bezier path between nodes
[ ] Edge updates when nodes move
[ ] Inherited edges (from collapse) show dashed style
[ ] ButtonEdge shows delete button on hover
[ ] ButtonEdge delete removes edge from store
[ ] GraphCanvas step (GRP-001-05) now has working edgeTypes
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

Test via integration:
1. Connect two nodes → floating edge appears
2. Drag source node → edge follows smoothly
3. Hover edge → delete button shows
4. Click delete → edge removed
5. Collapse group → inherited edges appear dashed

---

## 8. Git Workflow

### Commit

```
feat(edges): implement custom edge components (GRP-001-06)

- features/graph-editor/L2-canvas/edges/FloatingEdge.tsx
- features/graph-editor/L2-canvas/edges/ButtonEdge.tsx
- features/graph-editor/L2-canvas/edges/edge-helpers.ts
- Edge inheritance styling (dashed)
- Delete button on hover
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-06: Custom edges (FloatingEdge, ButtonEdge).
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@xyflow/react` | Edge rendering |
| `@/stores/graph-store` | For edge deletion |
| `@/schema/registry` | For connection validation |

---

## 10. Next Step

GRP-001-07 — L1 Page (GraphEditorPage orchestrator) — fetches data, translates via schemaToGraph, renders GraphCanvas.