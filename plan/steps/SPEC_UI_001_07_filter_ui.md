# Step 7: Replace Filter UI with DropdownMenu + Popover

**Spec:** SPEC_UI_001
**Phase:** 4 (Enhanced Features)
**Priority:** MEDIUM — Filter UX improvement

---

## 1. Migration Notes

> Migration from KnowledgeGraph.tsx lines 1600-1700: custom filter controls.

**Why migrate?**
- shadcn DropdownMenu/Popover provide accessible dropdown patterns
- Better keyboard navigation
- Consistent styling with other UI

---

## 2. Data Contract

```ts
interface FiltersSectionProps {
  relationTypes: string[];
  hiddenRelationTypes: string[];
  onToggleRelationType: (type: string) => void;
  filterText: string;
  onFilterTextChange: (text: string) => void;
  attributeFilter: { key: string; value: string } | null;
  onAttributeFilterChange: (filter: { key: string; value: string } | null) => void;
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── sidebar/
│           └── FiltersSection.tsx
```

---

## 4. Implementation

```tsx
// features/graph-editor/L2-canvas/sidebar/FiltersSection.tsx
// (Implementation already in file - verified)
```

---

## 5. Styles

Uses shadcn defaults + Tailwind for spacing.

---

## 6. Definition of Done

```
[ ] FiltersSection.tsx uses DropdownMenu for relation types
[ ] FiltersSection.tsx uses Popover for attribute filter
[ ] Text search filters nodes
[ ] Toggle relation type filters edges
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
test('filter dropdown works', async ({ page }) => {
  await page.goto('/graph');
  
  await page.click('button:has-text("Filter by Relation")');
  await expect(page.locator('[role="menu"]')).toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
refactor(ui): replace filter UI with shadcn (UI-001-07)

- FiltersSection uses DropdownMenu + Popover
- Connected to ui-store filters
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-07: Filter UI migration.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/dropdown-menu` | From UI-001-01 |
| `@/components/ui/popover` | From UI-001-01 |
| `@/components/ui/input` | From UI-001-01 |

---

## 10. Next Step

UI-001-08 — Replace node creation with Command + Popover.