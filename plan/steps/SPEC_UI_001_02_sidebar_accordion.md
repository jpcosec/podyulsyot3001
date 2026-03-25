# Step 2: Replace Sidebar Section with Accordion

**Spec:** SPEC_UI_001
**Phase:** 2 (Core Migration)
**Priority:** HIGH — High-impact visual component

---

## 1. Migration Notes

> Migration from KnowledgeGraph.tsx lines 283-303: `SidebarSection` component.

**Legacy code:**
```tsx
function SidebarSection({ title, open, onToggle, children }) {
  return (
    <section className="border border-outline-variant rounded-xl overflow-hidden">
      <button type="button" className="flex items-center justify-between w-full px-3 py-2 font-mono text-[10px] text-on-muted hover:text-on-surface bg-transparent" onClick={onToggle}>
        <span>{title}</span>
        <span>{open ? "-" : "+"}</span>
      </button>
      {open ? <div className="px-3 pb-3 flex flex-col gap-2">{children}</div> : null}
    </section>
  );
}
```

**Why migrate?**
- shadcn Accordion provides accessibility (keyboard nav, ARIA)
- Built-in animation and smooth transitions
- TypeScript support out of the box

---

## 2. Data Contract

```ts
// CanvasSidebarProps - after migration
interface CanvasSidebarProps {
  // Uses internal state via Accordion
}
```

---

## 3. Files to Modify

```
apps/review-workbench/src/
├── features/graph-editor/
│   └── L2-canvas/
│       └── sidebar/
│           └── CanvasSidebar.tsx  // Replace SidebarSection usage
```

---

## 4. Implementation

```tsx
// features/graph-editor/L2-canvas/sidebar/CanvasSidebar.tsx
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"

<Accordion type="multiple" defaultValue={["actions", "filters"]}>
  <AccordionItem value="actions">
    <AccordionTrigger className="font-mono text-[10px] uppercase tracking-[0.2em]">
      Actions
    </AccordionTrigger>
    <AccordionContent>
      <ActionsSection />
    </AccordionContent>
  </AccordionItem>
  
  <AccordionItem value="filters">
    <AccordionTrigger className="font-mono text-[10px] uppercase tracking-[0.2em]">
      Filters
    </AccordionTrigger>
    <AccordionContent>
      <FiltersSection />
    </AccordionContent>
  </AccordionItem>
  
  {/* ... more sections */}
</Accordion>
```

---

## 5. Styles

Keep existing Tailwind classes for visual continuity:
- `font-mono text-[10px] uppercase tracking-[0.2em]` on AccordionTrigger
- Gap and padding from legacy component

---

## 6. Definition of Done

```
[ ] CanvasSidebar uses shadcn Accordion
[ ] Sections expand/collapse independently (type="multiple")
[ ] Default open sections match legacy behavior
[ ] No visual regression vs old SidebarSection
[ ] Keyboard navigation works
[ ] No TypeScript errors
[ ] No console errors
```

---

## 7. E2E (TestSprite)

```ts
// e2e/graph-editor/sidebar.spec.ts
import { test, expect } from '@playwright/test';

test('accordion sections expand and collapse', async ({ page }) => {
  await page.goto('/graph');
  
  // Sidebar visible
  await expect(page.locator('[class*="accordion"]')).toBeVisible();
  
  // Click Actions
  await page.click('button:has-text("Actions")');
  await expect(page.locator('text=Auto Layout')).toBeVisible();
  
  // Click Filters
  await page.click('button:has-text("Filters")');
  await expect(page.locator('text=Relation Types')).toBeVisible();
});
```

---

## 8. Git Workflow

### Commit

```
refactor(ui): replace SidebarSection with shadcn Accordion (UI-001-02)

- Migrated CanvasSidebar to use Accordion component
- Preserved existing styling and behavior
- Added keyboard accessibility
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented UI-001-02: Sidebar accordion migration.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/accordion` | From UI-001-01 |

---

## 10. Next Step

UI-001-03 — Replace node edit modal with shadcn Sheet (NodeSheet).