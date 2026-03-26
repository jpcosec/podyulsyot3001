# Step 9: Create Hooks (Layout, EdgeInheritance, Keyboard)

**Spec:** SPEC_GRP_001
**Phase:** 3 (L2 Canvas)
**Priority:** MEDIUM — Utility hooks for automation

---

## 1. Migration Notes

> Not applicable — hooks are new code. No legacy equivalent.

**Why new?**
- Current `KnowledgeGraph.tsx` has no layout automation
- Blueprint mandates ELKjs for auto-layout
- Group collapse/expand not implemented in legacy

---

## 2. Data Contract

### useGraphLayout

```ts
interface LayoutOptions {
  direction?: 'LR' | 'TB' | 'RL' | 'BT';
  nodeSpacing?: number;
  rankSpacing?: number;
}

interface UseGraphLayoutResult {
  layout: (options?: LayoutOptions) => Promise<{ id: string; position: { x: number; y: number } }[]>;
}
```

### useEdgeInheritance

```ts
interface UseEdgeInheritanceResult {
  collapseGroup: (groupId: string) => void;
  expandGroup: (groupId: string) => void;
}
```

### useKeyboard

```ts
interface UseKeyboardResult {
  // Hook registers global listeners, no return value
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       ├── hooks/
│       │   ├── use-graph-layout.ts
│       │   ├── use-edge-inheritance.ts
│       │   └── use-keyboard.ts
│       └── workers/
│           └── elk.worker.ts       # Web Worker for ELK layout
```

---

## 4. Implementation

### Web Worker for ELK (elk.worker.ts)

```ts
// features/graph-editor/L2-canvas/workers/elk.worker.ts
import ELK from 'elkjs/lib/elk.bundled.js';

const elk = new ELK();

interface LayoutMessage {
  type: 'layout';
  payload: {
    nodes: Array<{ id: string; width?: number; height?: number }>;
    edges: Array<{ id: string; source: string; target: string }>;
    options: {
      direction?: 'LR' | 'TB' | 'RL' | 'BT';
      nodeSpacing?: number;
      rankSpacing?: number;
    };
  };
}

self.onmessage = async (event: MessageEvent<LayoutMessage>) => {
  if (event.data.type === 'layout') {
    const { nodes, edges, options } = event.data.payload;
    const { direction = 'LR', nodeSpacing = 50, rankSpacing = 100 } = options;
    
    const graph = {
      id: 'root',
      layoutOptions: {
        'elk.direction': direction,
        'elk.spacing.nodeNode': nodeSpacing,
        'elk.spacing.rankRank': rankSpacing,
      },
      children: nodes.map(node => ({
        id: node.id,
        width: node.width ?? 170,
        height: node.height ?? 68,
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        sources: [edge.source],
        targets: [edge.target],
      })),
    };
    
    const layoutedGraph = await elk.layout(graph);
    
    const updates = (layoutedGraph.children ?? [])
      .filter((node: any) => node.x !== undefined && node.y !== undefined)
      .map((node: any) => ({
        id: node.id,
        position: { x: node.x, y: node.y },
      }));
    
    self.postMessage({ type: 'result', payload: updates });
  }
};

export {};
```

### Hook that uses Web Worker

```ts
// features/graph-editor/L2-canvas/hooks/use-graph-layout.ts
import { useCallback, useRef, useEffect } from 'react';
import { useGraphStore } from '@/stores/graph-store';

interface LayoutOptions {
  direction?: 'LR' | 'TB' | 'RL' | 'BT';
  nodeSpacing?: number;
  rankSpacing?: number;
}

export function useGraphLayout() {
  const nodes = useGraphStore(s => s.nodes);
  const edges = useGraphStore(s => s.edges);
  const updateNode = useGraphStore(s => s.updateNode);
  const workerRef = useRef<Worker | null>(null);
  
  // Initialize worker on mount
  useEffect(() => {
    workerRef.current = new Worker(
      new URL('./workers/elk.worker.ts', import.meta.url),
      { type: 'module' }
    );
    
    return () => {
      workerRef.current?.terminate();
    };
  }, []);
  
  const layout = useCallback((options: LayoutOptions = {}): Promise<Array<{ id: string; position: { x: number; y: number } }>> => {
    return new Promise((resolve) => {
      if (!workerRef.current) {
        console.error('Layout worker not initialized');
        resolve([]);
        return;
      }
      
      const handler = (event: MessageEvent) => {
        const updates = event.data.payload;
        // Apply updates to store
        updates.forEach(({ id, position }: { id: string; position: { x: number; y: number } }) => {
          updateNode(id, { position });
        });
        workerRef.current?.removeEventListener('message', handler);
        resolve(updates);
      };
      
      workerRef.current.addEventListener('message', handler);
      
      workerRef.current.postMessage({
        type: 'layout',
        payload: {
          nodes: nodes.map(node => ({
            id: node.id,
            width: node.data?.width ?? 170,
            height: node.data?.height ?? 68,
          })),
          edges: edges.map(edge => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
          })),
          options,
        },
      });
    });
  }, [nodes, edges, updateNode]);
  
  return { layout };
}
```

```ts
// features/graph-editor/L2-canvas/hooks/use-edge-inheritance.ts
import { useCallback } from 'react';
import { useGraphStore } from '@/stores/graph-store';

export function useEdgeInheritance() {
  const nodes = useGraphStore(s => s.nodes);
  const edges = useGraphStore(s => s.edges);
  const updateNode = useGraphStore(s => s.updateNode);
  const updateEdge = useGraphStore(s => s.updateEdge);
  
  const collapseGroup = useCallback((groupId: string) => {
    const childNodes = nodes.filter(n => n.parentId === groupId);
    const childIds = new Set(childNodes.map(n => n.id));
    
    // 1. Hide child nodes (visual-only: no undo stack entry)
    childNodes.forEach(child => {
      updateNode(child.id, { hidden: true }, { isVisualOnly: true });
    });
    
    // 2. Create inherited edges (visual-only: no undo stack entry)
    const groupEdges = edges.filter(e => 
      childIds.has(e.source) || childIds.has(e.target)
    );
    
    groupEdges.forEach(edge => {
      const wasHidden = edge.hidden;
      const newSource = childIds.has(edge.source) ? groupId : edge.source;
      const newTarget = childIds.has(edge.target) ? groupId : edge.target;
      
      if (newSource !== newTarget) {
        updateEdge(edge.id, {
          source: newSource,
          target: newTarget,
          hidden: wasHidden,
          data: {
            ...edge.data,
            _originalSource: edge.source,
            _originalTarget: edge.target,
            relationType: edge.data?.relationType === 'inherited' 
              ? 'inherited' 
              : edge.data?.relationType,
          },
        }, { isVisualOnly: true });
      }
    });
    
    // 3. Update group node (visual-only: no undo stack entry)
    const groupNode = nodes.find(n => n.id === groupId);
    if (groupNode) {
      updateNode(groupId, { 
        data: { ...groupNode.data, collapsed: true },
        style: { ...groupNode.style, height: 48 },
      }, { isVisualOnly: true });
    }
  }, [nodes, edges, updateNode, updateEdge]);
  
  const expandGroup = useCallback((groupId: string) => {
    const childNodes = nodes.filter(n => n.parentId === groupId);
    const childIds = new Set(childNodes.map(n => n.id));
    
    // 1. Show child nodes (visual-only: no undo stack entry)
    childNodes.forEach(child => {
      updateNode(child.id, { hidden: false }, { isVisualOnly: true });
    });
    
    // 2. Restore original edges (visual-only: no undo stack entry)
    edges
      .filter(e => e.data?._originalSource || e.data?._originalTarget)
      .forEach(edge => {
        updateEdge(edge.id, {
          source: edge.data._originalSource ?? edge.source,
          target: edge.data._originalTarget ?? edge.target,
          hidden: false,
          data: {
            ...edge.data,
            _originalSource: undefined,
            _originalTarget: undefined,
          },
        }, { isVisualOnly: true });
      });
    
    // 3. Update group node (visual-only: no undo stack entry)
    const groupNode = nodes.find(n => n.id === groupId);
    if (groupNode) {
      updateNode(groupId, { 
        data: { ...groupNode.data, collapsed: false },
        style: { ...groupNode.style, height: undefined },
      }, { isVisualOnly: true });
    }
  }, [nodes, edges, updateNode, updateEdge]);
  
  return { collapseGroup, expandGroup };
}
```

```ts
// features/graph-editor/L2-canvas/hooks/use-keyboard.ts
import { useEffect } from 'react';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';

export function useKeyboard() {
  const editorState = useUIStore(s => s.editorState);
  const setEditorState = useUIStore(s => s.setEditorState);
  const focusedNodeId = useUIStore(s => s.focusedNodeId);
  const setFocusedNode = useUIStore(s => s.setFocusedNode);
  
  const undo = useGraphStore(s => s.undo);
  const redo = useGraphStore(s => s.redo);
  
  // NOTE: Delete key handling is done by ReactFlow internally via onNodesDelete/onEdgesDelete
  // Do NOT implement manual Delete handling here - it would duplicate functionality
  
  // Enter - open node editor
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && editorState === 'browse' && focusedNodeId) {
        setEditorState('edit_node');
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [editorState, focusedNodeId, setEditorState]);
  
  // Escape - close editor
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (editorState === 'edit_node' || editorState === 'edit_relation') {
          setFocusedNode(null);
          setEditorState('browse');
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [editorState, setEditorState, setFocusedNode]);
  
  // Ctrl+Z - Undo
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (editorState === 'browse') {
          undo();
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [editorState, undo]);
  
  // Ctrl+Y / Ctrl+Shift+Z - Redo
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        if (editorState === 'browse') {
          redo();
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [editorState, redo]);
}
```

---

---

## 5. Styles

Hooks are pure logic — no styles. Layout updates positions in store; keyboard attaches event listeners.

---

## 6. Definition of Done

```
[ ] use-graph-layout.ts exports useGraphLayout hook
[ ] elk.worker.ts runs ELK layout in Web Worker (not main thread)
[ ] use-graph-layout.layout() repositions nodes asynchronously
[ ] use-edge-inheritance.ts exports collapseGroup/expandGroup
[ ] collapseGroup uses isVisualOnly: true (no undo entry)
[ ] expandGroup uses isVisualOnly: true (no undo entry)
[ ] use-keyboard.ts attaches Enter, Escape handlers
[ ] use-keyboard.ts attaches Ctrl+Z/Ctrl+Y for undo/redo
[ ] use-keyboard.ts does NOT handle Delete (ReactFlow handles it via onNodesDelete)
[ ] No TypeScript errors
[ ] No memory leaks from event listeners
```

---

## 7. E2E (TestSprite)

```ts
// e2e/graph-editor/hooks.spec.ts
import { test, expect } from '@playwright/test';

test('keyboard shortcuts work', async ({ page }) => {
  await page.goto('/graph');
  
  // Select a node first via UI
  await page.click('[data-testid="node-person-1"]');
  
  // Press Delete
  await page.keyboard.press('Delete');
  
  // Node should be removed (test depends on selection state)
});

test('undo restores deleted node', async ({ page }) => {
  await page.goto('/graph');
  
  // Delete node
  await page.click('[data-testid="node-person-1"]');
  await page.keyboard.press('Delete');
  
  // Undo
  await page.keyboard.press('Control+z');
  
  // Node should reappear
  await expect(page.locator('[data-testid="node-person-1"]')).toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
feat(hooks): implement utility hooks (GRP-001-09)

- L2-canvas/hooks/use-graph-layout.ts with ELKjs
- L2-canvas/hooks/use-edge-inheritance.ts for groups
- L2-canvas/hooks/use-keyboard.ts for shortcuts
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-09: Graph utility hooks.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `elkjs` | Graph layout algorithm (runs in Web Worker) |
| `@xyflow/react` | ReactFlow (provides onNodesDelete/onEdgesDelete) |

---

## 10. Next Step

GRP-001-10 — L1 Page Orchestrator — connects L2 components and handles data loading.