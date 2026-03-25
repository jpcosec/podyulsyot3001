# Step 5: Replace PropertyValueInput with Shadcn Inputs

**Spec:** SPEC_UI_001
**Phase:** 3 (Property Components)
**Priority:** MEDIUM — Form input consolidation

---

## 1. Migration Notes

> Migration from KnowledgeGraph.tsx lines 465-549: `PropertyValueInput` component.

**Why migrate?**
- shadcn Input/Select/Textarea provide consistent styling
- Better accessibility and keyboard navigation
- Reuses PropertyEditor from GRP-001-04

---

## 2. Data Contract

```ts
interface PropertyPair {
  key: string;
  value: string;
  dataType: AttributeType;
}

type AttributeType = "string" | "text_markdown" | "number" | "date" | "datetime" | "boolean" | "enum" | "enum_open";
```

---

## 3. Files to Modify

```
apps/review-workbench/src/
├── components/
│   └── content/
│       └── PropertyEditor.tsx  // Already in GRP-001-04
```

---

## 4. Implementation

```tsx
// Already implemented in GRP-001-04 - verify usage
// features/graph-editor/L2-canvas/sidebar/CanvasSidebar.tsx
import { PropertyEditor } from "@/components/content/PropertyEditor"
```

---

## 5. Styles

Uses shadcn component defaults + Tailwind for layout.

---

## 6. Definition of Done

```
[ ] PropertyEditor uses shadcn Input, Textarea, Select, Checkbox
[ ] Each dataType renders appropriate input
[ ] Add Property button works
[ ] No TypeScript errors
```

---

## 7. E2E (TestSprite)

```ts
test('property editor renders inputs', async ({ page }) => {
  await page.goto('/graph');
  await page.click('[data-testid="node-person-1"]');
  
  // Check Input renders
  await expect(page.locator('input[placeholder="key"]')).toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
refactor(ui): replace property inputs with shadcn (UI-001-05)

- Integrated PropertyEditor from GRP-001-04
- Uses Input, Textarea, Select, Checkbox
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-05: Property input migration.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/input` | From UI-001-01 |
| `@/components/ui/textarea` | From UI-001-01 |
| `@/components/ui/select` | From UI-001-01 |
| `@/components/ui/checkbox` | Default shadcn |
| `PropertyEditor` | From GRP-001-04 |

---

## 10. Next Step

UI-001-06 — Replace delete confirmation with shadcn AlertDialog.