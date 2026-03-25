# Step 11: CSS Theming (xy-theme.css)

**Spec:** SPEC_GRP_001
**Phase:** 6 (CSS/Theming)
**Priority:** LOW — Visual styling layer

---

## 1. Migration Notes

> Not applicable — theming is new CSS. No legacy equivalent.

**Why new?**
- Current `KnowledgeGraph.tsx` uses inline Tailwind classes
- Blueprint mandates CSS custom properties for theming
- Enables dark mode and type-based colors via data attributes

---

## 2. Data Contract

N/A — CSS file, no TypeScript contracts.

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── xy-theme.css
```

---

## 4. Implementation

```css
/* features/graph-editor/L2-canvas/xy-theme.css */

/* ========== Theme Tokens ========== */
.react-flow {
  /* Selection state */
  --xy-theme-selected: #F57DBD;
  --xy-theme-hover: #C5C5C5;
  --xy-theme-edge-hover: black;
  
  /* Node defaults */
  --xy-node-border-default: 1px solid #EDEDED;
  --xy-node-border-radius-default: 8px;
  --xy-node-boxshadow-default:
    0px 3.54px 4.55px 0px #00000005,
    0px 3.54px 4.55px 0px #0000000D;
  
  /* Handles */
  --xy-handle-background-color-default: #ffffff;
  --xy-handle-border-color-default: #AAAAAA;
  --xy-handle-size-default: 8px;
  --xy-handle-size-touch: 20px;
}

/* ========== Node Type Colors ========== */
/* Referenced by registry colorToken */

.react-flow__node[data-type="person"] { 
  --node-color: #8B5CF6; /* purple-500 */
}

.react-flow__node[data-type="skill"] { 
  --node-color: #06B6D4; /* cyan-500 */
}

.react-flow__node[data-type="project"] { 
  --node-color: #F59E0B; /* amber-500 */
}

.react-flow__node[data-type="publication"] { 
  --node-color: #FFB5AB; /* coral */
}

.react-flow__node[data-type="concept"] { 
  --node-color: #747578; /* gray-500 */
}

.react-flow__node[data-type="document"] { 
  --node-color: #00F2FF; /* cyan-400 */
}

.react-flow__node[data-type="section"] { 
  --node-color: #FFAA00; /* amber-400 */
}

.react-flow__node[data-type="entry"] { 
  --node-color: #747578; /* gray-500 */
}

/* Group nodes */
.react-flow__node[data-type="group"] { 
  --node-color: #747578;
}

/* Error nodes */
.react-flow__node[data-type="error"] { 
  --node-color: #EF4444; /* red-500 */
}

/* ========== Node Base Styles ========== */
.react-flow__node {
  border-color: var(--node-color, var(--xy-node-border-default));
  border-width: 2px;
  border-style: solid;
  border-radius: var(--xy-node-border-radius-default);
  box-shadow: var(--xy-node-boxshadow-default);
}

/* Selected state */
.react-flow__node.selectable.selected {
  border-color: var(--xy-theme-selected);
  box-shadow: 0 0 0 2px var(--xy-theme-selected);
}

/* Hover state */
.react-flow__node.selectable:hover {
  border-color: var(--xy-theme-hover);
}

/* ========== Edge Styles ========== */

/* Default edge */
.react-flow__edge-path {
  stroke: #334155;
  stroke-width: 1.5;
}

/* Inherited edge (from group collapse) */
.react-flow__edge.inherited .react-flow__edge-path {
  stroke-dasharray: 3 4;
  opacity: 0.5;
  stroke: rgba(116, 117, 120, 0.7);
}

/* Edge hover */
.react-flow__edge:hover .react-flow__edge-path {
  stroke: var(--xy-theme-edge-hover);
}

/* ========== Dark Mode ========== */
.react-flow.dark {
  --xy-node-boxshadow-default:
    0px 3.54px 4.55px 0px rgba(255, 255, 255, 0.05),
    0px 3.54px 4.55px 0px rgba(255, 255, 255, 0.13);
  
  --xy-node-border-default: 1px solid #374151;
  
  --xy-handle-background-color-default: #1F2937;
  --xy-handle-border-color-default: #4B5563;
}

/* ========== Touch Support ========== */
@media (pointer: coarse) {
  .react-flow__handle {
    width: var(--xy-handle-size-touch);
    height: var(--xy-handle-size-touch);
  }
}

/* ========== Group Node ========== */
.react-flow__node.group {
  border-style: dashed;
  background: transparent;
}

/* ========== Utility Classes ========== */
.react-flow__node .opacity-30 {
  opacity: 0.3;
}

.react-flow__node .opacity-100 {
  opacity: 1;
}
```

---

## Files Created

```
features/graph-editor/L2-canvas/
  xy-theme.css
```

---

---

## 5. Styles (Terran Command)

This IS the stylesheet — no additional styles needed.

---

## 6. Definition of Done

```
[ ] xy-theme.css exists in L2-canvas/
[ ] CSS custom properties defined for node colors
[ ] .inherited edge class applies dashed style
[ ] Dark mode overrides via .react-flow.dark selector
[ ] Touch support via @media (pointer: coarse)
[ ] No console errors on ReactFlow load
```

---

## 7. E2E (TestSprite)

```ts
// e2e/graph-editor/theming.spec.ts
import { test, expect } from '@playwright/test';

test('node colors match type', async ({ page }) => {
  await page.goto('/graph');
  
  // Person node should have purple border
  const personNode = page.locator('.react-flow__node').first();
  await expect(personNode).toHaveCSS('border-color', 'rgb(139, 92, 246)');
});

test('inherited edges are dashed', async ({ page }) => {
  await page.goto('/graph');
  
  // Collapse a group first (requires group to exist)
  // Then check edge class
  await expect(page.locator('.react-flow__edge.inherited .react-flow__edge-path'))
    .toHaveCSS('stroke-dasharray', '3 4');
});
```

---

## 8. Git Workflow

### Commit

```
feat(theming): add xy-theme.css for node editor (GRP-001-11)

- L2-canvas/xy-theme.css with CSS custom properties
- Node type colors via data-type selectors
- Dark mode and touch support
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-11: CSS theming for node editor.
```

---

## 9. Dependencies

N/A — Pure CSS, no npm dependencies.

---

## 10. Next Step

Complete GRP-001 — Review all steps and verify no conflicts with Guide principles. Begin UI-001 parallel track for shadcn migration.