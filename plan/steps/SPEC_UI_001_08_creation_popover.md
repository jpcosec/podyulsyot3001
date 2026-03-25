# Step 8: Replace Creation List with Command + Popover

**Spec:** SPEC_UI_001
**Phase:** 4 (Enhanced Features)
**Priority:** HIGH — Core creation UX

---

## 1. Migration Notes

> Migration from KnowledgeGraph.tsx lines 1730-1800: simple list of creation buttons.

**Why migrate?**
- shadcn Command provides searchable dropdown
- Better UX for many node types
- Keyboard navigation support

---

## 2. Data Contract

```ts
interface NodeTemplate {
  name: string;
  category: string;
  defaults: Record<string, string>;
}

interface CreationSectionProps {
  templates: NodeTemplate[];
  onCreateNode: (template: NodeTemplate) => void;
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── sidebar/
│           └── CreationSection.tsx
```

---

## 4. Implementation

```tsx
// features/graph-editor/L2-canvas/sidebar/CreationSection.tsx
// (Implementation verified)
```

---

## 5. Styles

Uses shadcn Command + Popover defaults.

---

## 6. Definition of Done

```
[ ] CreationSection uses Command + Popover
[ ] Search filters node types
[ ] Click creates node
[ ] Keyboard navigation works
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
test('creation command searches', async ({ page }) => {
  await page.goto('/graph');
  
  await page.click('button:has-text("Add Node")');
  await page.fill('[role="combobox"] input', 'person');
  await expect(page.locator('text=Person')).toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
refactor(ui): replace creation list with Command (UI-001-08)

- CreationSection uses Command + Popover
- Searchable node type selection
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-08: Creation UI migration.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/command` | From UI-001-01 |
| `@/components/ui/popover` | From UI-001-01 |

---

## 10. Next Step

UI-001-09 — Replace context menu with shadcn ContextMenu.