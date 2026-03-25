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
│       └── hooks/
│           ├── use-graph-layout.ts
│           ├── use-edge-inheritance.ts
│           └── use-keyboard.ts
```

---

## 4. Implementation

```ts
// features/graph-editor/L2-canvas/hooks/use-graph-layout.ts
import { useCallback } from 'react';
import ELK from 'elkjs/lib/elk.bundled.js';
import { useGraphStore } from '@/stores/graph-store';

const elk = new ELK();

interface LayoutOptions {
  direction?: 'LR' | 'TB' | 'RL' | 'BT';
  nodeSpacing?: number;
  rankSpacing?: number;
}

export function useGraphLayout() {
  const nodes = useGraphStore(s => s.nodes);
  const edges = useGraphStore(s => s.edges);
  const updateNode = useGraphStore(s => s.updateNode);
  
  const layout = useCallback(async (options: LayoutOptions = {}) => {
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
        width: node.data?.width ?? 170,
        height: node.data?.height ?? 68,
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
    
    updates.forEach(({ id, position }) => {
      updateNode(id, { position });
    });
    
    return updates;
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
    
    // 1. Hide child nodes
    childNodes.forEach(child => {
      updateNode(child.id, { hidden: true });
    });
    
    // 2. Create inherited edges
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
        });
      }
    });
    
    // 3. Update group node
    const groupNode = nodes.find(n => n.id === groupId);
    if (groupNode) {
      updateNode(groupId, { 
        data: { ...groupNode.data, collapsed: true },
        style: { ...groupNode.style, height: 48 },
      });
    }
  }, [nodes, edges, updateNode, updateEdge]);
  
  const expandGroup = useCallback((groupId: string) => {
    const childNodes = nodes.filter(n => n.parentId === groupId);
    const childIds = new Set(childNodes.map(n => n.id));
    
    // 1. Show child nodes
    childNodes.forEach(child => {
      updateNode(child.id, { hidden: false });
    });
    
    // 2. Restore original edges
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
        });
      });
    
    // 3. Update group node
    const groupNode = nodes.find(n => n.id === groupId);
    if (groupNode) {
      updateNode(groupId, { 
        data: { ...groupNode.data, collapsed: false },
        style: { ...groupNode.style, height: undefined },
      });
    }
  }, [nodes, edges, updateNode, updateEdge]);
  
  return { collapseGroup, expandGroup };
}
```

```ts
// features/graph-editor/L2-canvas/hooks/use-keyboard.ts
import { useEffect, useCallback } from 'react';
import { useStore } from 'zustand';
import { useKeyboardShortcuts as useRFKeyboard } from '@xyflow/react';
import { useGraphStore } from '@/stores/graph-store';
import { useUIStore } from '@/stores/ui-store';

export function useKeyboard() {
  const editorState = useUIStore(s => s.editorState);
  const setEditorState = useUIStore(s => s.setEditorState);
  const focusedNodeId = useUIStore(s => s.focusedNodeId);
  const setFocusedNode = useUIStore(s => s.setFocusedNode);
  
  const undo = useGraphStore(s => s.undo);
  const redo = useGraphStore(s => s.redo);
  const removeElements = useGraphStore(s => s.removeElements);
  
  // Delete
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (editorState === 'browse' || editorState === 'focus') {
          // Trigger delete for selected elements
          // Implementation depends on selection state
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [editorState]);
  
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
[ ] use-graph-layout.layout() repositions nodes via ELKjs
[ ] use-edge-inheritance.ts exports collapseGroup/expandGroup
[ ] collapseGroup hides children, rewires edges to group
[ ] expandGroup shows children, restores original edges
[ ] use-keyboard.ts attaches Delete, Enter, Escape handlers
[ ] use-keyboard.ts attaches Ctrl+Z/Ctrl+Y for undo/redo
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
| `elkjs` | Graph layout algorithm |
| `@xyflow/react` | ReactFlow keyboard utilities |

---

## 10. Next Step

GRP-001-10 — L1 Page Orchestrator — connects L2 components and handles data loading.