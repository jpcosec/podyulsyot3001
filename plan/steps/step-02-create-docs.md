# Step 02: Create Updated Documentation

**Context:** After the refactor, documentation needs to reflect the new architecture.

---

## 1. Purpose

- Update README with new architecture overview
- Document the L1/L2 split in ARCHITECTURE.md
- Create API documentation for new components

---

## 2. Files to Update

```
docs/
├── README.md                    # Main project README
├── graph-editor/
│   ├── README.md               # Graph editor module docs
│   ├── architecture.md         # L1/L2 architecture
│   └── api/
│       ├── stores.md           # Graph/UI store APIs
│       ├── components.md       # Component API docs
│       └── hooks.md            # Hooks API docs
```

---

## 3. Content Templates

### docs/graph-editor/README.md

```markdown
# Graph Editor

Knowledge graph visualization and editing component.

## Architecture

- **L1 (App Layer):** `GraphEditorPage` - Data loading, schema translation
- **L2 (Canvas Layer):** `GraphEditor` - Sidebar, panels, controls
- **L3 (Content Layer):** Nodes, edges, property editors

## Usage

\`\`\`tsx
import { GraphEditorPage } from '@/features/graph-editor/L1-app/GraphEditorPage';

export default function GraphPage() {
  return <GraphEditorPage />;
}
\`\`\`
```

### docs/graph-editor/architecture.md

```markdown
# Graph Editor Architecture

## Layer Responsibilities

### L1 - Application Layer
- Fetches raw data from API
- Translates schema to AST via `schemaToGraph`
- Handles save via `graphToDomain`
- Delegates rendering to L2

### L2 - Canvas Layer
- Manages ReactFlow canvas
- Owns sidebar, panels, controls
- Handles keyboard shortcuts
- Applies layout algorithms

### L3 - Content Layer
- Node components (SimpleNodeCard, GroupNode)
- Edge components (FloatingEdge, ButtonEdge)
- Property editors

## State Management

- `graph-store`: nodes, edges, undo/redo, dirty state
- `ui-store`: editorState, focusedId, filters, sidebar
```

---

## 4. Verification

- [ ] README.md mentions new architecture
- [ ] docs/graph-editor/ exists with README
- [ ] API docs cover stores, components, hooks
- [ ] No broken links

---

## 5. Next Step

step-03-cleanup-plan — Clean up temporary planning files.