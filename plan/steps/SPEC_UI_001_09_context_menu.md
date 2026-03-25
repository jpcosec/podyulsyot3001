# Step 9: Add ContextMenu to Nodes

**Spec:** SPEC_UI_001
**Phase:** 4 (Enhanced Features)
**Priority:** MEDIUM — Right-click actions

---

## 1. Migration Notes

> NEW feature - not replacing legacy code. KnowledgeGraph.tsx has no context menu.

**Why add?**
- Common UX pattern for node actions
- Quick access to Edit, Copy, Delete
- Keyboard shortcuts displayed

---

## 2. Data Contract

N/A — Context menu wraps existing node component.

---

## 3. Files to Modify

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── nodes/
│           └── SimpleNodeCard.tsx  // Wrap with ContextMenu
```

---

## 4. Implementation

```tsx
// In SimpleNodeCard.tsx
import { ContextMenu, ContextMenuContent, ContextMenuItem, ContextMenuSeparator, ContextMenuShortcut, ContextMenuTrigger } from "@/components/ui/context-menu"

<ContextMenu>
  <ContextMenuTrigger disabled={selected}>
    <div className="...">{/* node content */}</div>
  </ContextMenuTrigger>
  <ContextMenuContent>
    <ContextMenuItem onClick={() => openNodeEditor(data.id)}>
      Edit <ContextMenuShortcut>Enter</ContextMenuShortcut>
    </ContextMenuItem>
    <ContextMenuItem onClick={() => openFocusMode(data.id)}>
      Focus Neighborhood
    </ContextMenuItem>
    <ContextMenuSeparator />
    <ContextMenuItem onClick={() => copyNode(data.id)}>
      Copy <ContextMenuShortcut>Ctrl+C</ContextMenuShortcut>
    </ContextMenuItem>
    <ContextMenuItem onClick={() => triggerDelete(data)}>
      Delete <ContextMenuShortcut>Del</ContextMenuShortcut>
    </ContextMenuItem>
  </ContextMenuContent>
</ContextMenu>
```

**Note:** ContextMenu may conflict with ReactFlow selection - wrap carefully.

---

## 5. Styles

Uses shadcn ContextMenu defaults.

---

## 6. Definition of Done

```
[ ] SimpleNodeCard wrapped with ContextMenu
[ ] Right-click shows menu
[ ] All menu items trigger correct actions
[ ] No conflict with ReactFlow selection
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
test('context menu appears on right-click', async ({ page }) => {
  await page.goto('/graph');
  
  await page.click('[data-testid="node-person-1"]', { button: 'right' });
  await expect(page.locator('text=Edit')).toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
feat(ui): add context menu to nodes (UI-001-09)

- ContextMenu on SimpleNodeCard
- Edit, Focus, Copy, Delete actions
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-09: Context menu for nodes.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/context-menu` | From UI-001-01 |

---

## 10. Next Step

UI-001-10 — Add CommandDialog for global search/command palette.