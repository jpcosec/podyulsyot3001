# TestSprite Product Specification

**Context:** E2E testing framework for the graph editor refactor.

---

## 1. Overview

TestSprite is our end-to-end testing framework based on Playwright. It provides:
- Browser automation for full user flows
- Component interaction testing
- Visual regression detection
- Test reporting and CI integration

---

## 2. Graph Editor Test Scopes

### Scope 1: Core Rendering
- Graph loads with nodes and edges
- Nodes render with correct labels
- Edges connect properly
- Pan and zoom work

### Scope 2: Node Interactions
- Click node selects it
- Double-click opens inspector
- Drag node repositions it
- Context menu appears on right-click

### Scope 3: Edge Interactions
- Click edge opens inspector
- Edge labels display correctly
- Hover shows edge highlight

### Scope 4: Sidebar Functionality
- Accordion sections expand/collapse
- Filter controls work
- Creation popover searches
- View controls change display

### Scope 5: Inspector Panels
- Node inspector opens/closes
- Property editing saves
- Edge inspector opens/closes
- Delete confirmation works

### Scope 6: Keyboard Shortcuts
- Ctrl+K opens command palette
- Escape closes modals
- Ctrl+Z undoes action
- Ctrl+Y redoes action

### Scope 7: Data Operations
- Save persists changes
- Undo reverts changes
- Redo reapplies changes
- Loading states display

---

## 3. Test File Structure

```
e2e/
├── graph-editor/
│   ├── rendering.spec.ts       # Scope 1
│   ├── nodes.spec.ts           # Scope 2
│   ├── edges.spec.ts           # Scope 3
│   ├── sidebar.spec.ts         # Scope 4
│   ├── panels.spec.ts          # Scope 5
│   ├── keyboard.spec.ts        # Scope 6
│   └── data-operations.spec.ts # Scope 7
└── playwright.config.ts
```

---

## 4. Testing Patterns

### Setup

```ts
// e2e/graph-editor/utils.ts
import { test as base } from '@playwright/test';

export const test = base.extend({
  // Custom fixtures
});

test.beforeEach(async ({ page }) => {
  await page.goto('/graph');
  // Wait for graph to load
  await page.waitForSelector('.react-flow__node');
});
```

### Node Selection

```ts
test('selects node on click', async ({ page }) => {
  await page.click('[data-testid="node-person-1"]');
  await expect(page.locator('[data-testid="node-person-1"]'))
    .toHaveClass(/selected/);
});
```

### Panel Interaction

```ts
test('opens inspector and edits', async ({ page }) => {
  await page.click('[data-testid="node-person-1"]');
  await expect(page.locator('[role="dialog"]')).toBeVisible();
  
  await page.fill('#name', 'New Name');
  await page.click('button:has-text("Save")');
  
  await expect(page.locator('[data-testid="node-person-1"]'))
    .toContainText('New Name');
});
```

---

## 5. CI Configuration

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test e2e/graph-editor/
        env:
          BASE_URL: http://localhost:3000
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 6. Running Tests

```bash
# All tests
npx playwright test e2e/graph-editor/

# Specific scope
npx playwright test e2e/graph-editor/nodes.spec.ts

# UI mode (interactive)
npx playwright test e2e/graph-editor/ --ui

# With coverage
npx playwright test e2e/graph-editor/ --coverage
```

---

## 7. Definition of Done

- [ ] playwright.config.ts configured
- [ ] All 7 scopes have test coverage
- [ ] CI pipeline runs tests on PR
- [ ] Test reports accessible
- [ ] >80% pass rate on first run

---

## 8. Maintenance

- Review tests after each UI change
- Update selectors when components change
- Add new tests for new features
- Monitor flakiness in CI

---

## Reference

- Playwright: https://playwright.dev/
- TestSprite internal docs (if available)
