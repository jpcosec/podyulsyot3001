# Step 3: Node Type Registry

**Spec:** SPEC_GRP_001  
**Phase:** 2 (Type System)  
**Priority:** HIGH — Required for schemaToGraph validation  
**Dependency:** GRP-001-02 (schema lib imports registry)

---

## 1. Migration Notes

> Not applicable — this is new code. No legacy component to extract.

**Why this step exists:**
- Blueprint: "Node Type Registry — reemplaza CATEGORY_COLORS + NODE_TEMPLATES hardcoded"
- Current KnowledgeGraph.tsx has hardcoded `CATEGORY_COLORS` (lines 149-176) and `NODE_TEMPLATES` (lines 190-199)
- Registry provides: validation (Zod), sanitization (DOMPurify), connection rules, render tiers

---

## 2. Data Contract

### NodeTypeDefinition

```ts
interface NodeTypeDefinition {
  typeId: string;           // unique identifier: "person", "skill", "project"
  label: string;           // display name: "Person", "Skill"
  icon: string;           // lucide icon name: "user", "wrench"
  category: string;       // grouping: "entity", "content", "component"
  colorToken: string;     // CSS variable: "token-person"
  payloadSchema: z.ZodSchema;  // validation rules
  sanitizer?: (payload: unknown) => unknown;  // DOMPurify or custom
  renderers: {
    dot: React.ComponentType<{ colorToken: string }>;     // zoom < 0.4
    label: React.ComponentType<{ title: string; icon: string }>;  // zoom 0.4-0.9
    detail: React.ComponentType<any>;                     // zoom >= 0.9
  };
  defaultSize: { width: number; height: number };
  allowedConnections: string[];  // typeIds that can receive connections
}
```

### Registry API

```ts
interface NodeTypeRegistry {
  register(def: NodeTypeDefinition): void;
  get(typeId: string): NodeTypeDefinition | undefined;
  getRenderer(typeId: string, zoomLevel: 'dot' | 'label' | 'detail'): React.ComponentType;
  validatePayload(typeId: string, payload: unknown): z.SafeParseReturnType<any, any>;
  sanitizePayload(typeId: string, payload: unknown): unknown;
  canConnect(sourceTypeId: string, targetTypeId: string): boolean;
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── schema/
│   ├── registry.ts            # NodeTypeRegistry class + singleton
│   ├── registry.types.ts      # NodeTypeDefinition interface
│   └── register-defaults.ts   # Default node type registrations
```

---

## 4. Implementation

### schema/registry.types.ts

```ts
import { z } from 'zod';

export interface NodeTypeDefinition {
  typeId: string;
  label: string;
  icon: string;
  category: string;
  colorToken: string;
  payloadSchema: z.ZodSchema;
  sanitizer?: (payload: unknown) => unknown;
  renderers: {
    dot: React.ComponentType<{ colorToken: string }>;
    label: React.ComponentType<{ title: string; icon: string }>;
    detail: React.ComponentType<any>;
  };
  defaultSize: { width: number; height: number };
  allowedConnections: string[];
}

export interface PayloadSchema {
  [key: string]: z.ZodTypeAny;
}
```

### schema/registry.ts

```ts
import type { NodeTypeDefinition } from './registry.types';
import { z } from 'zod';

class NodeTypeRegistry {
  private types = new Map<string, NodeTypeDefinition>();
  
  register(def: NodeTypeDefinition): void {
    if (this.types.has(def.typeId)) {
      console.warn(`Overriding existing node type: ${def.typeId}`);
    }
    this.types.set(def.typeId, def);
  }
  
  get(typeId: string): NodeTypeDefinition | undefined {
    return this.types.get(typeId);
  }
  
  getRenderer(typeId: string, zoomLevel: 'dot' | 'label' | 'detail'): React.ComponentType {
    const def = this.types.get(typeId);
    if (!def) {
      throw new Error(`Unknown node type: ${typeId}`);
    }
    return def.renderers[zoomLevel];
  }
  
  validatePayload(typeId: string, payload: unknown): z.SafeParseReturnType<any, any> {
    const def = this.types.get(typeId);
    if (!def) {
      return { 
        success: false, 
        error: new Error(`Unknown type: ${typeId}`),
        data: null,
      } as any;
    }
    return def.payloadSchema.safeParse(payload);
  }
  
  sanitizePayload(typeId: string, payload: unknown): unknown {
    const def = this.types.get(typeId);
    if (!def) return payload;
    return def.sanitizer ? def.sanitizer(payload) : payload;
  }
  
  canConnect(sourceTypeId: string, targetTypeId: string): boolean {
    const source = this.types.get(sourceTypeId);
    if (!source) return false;
    return source.allowedConnections.includes(targetTypeId);
  }
  
  getAll(): NodeTypeDefinition[] {
    return Array.from(this.types.values());
  }
}

export const registry = new NodeTypeRegistry();
```

### schema/register-defaults.ts

```ts
import { registry } from './registry';
import { z } from 'zod';

// Person node
registry.register({
  typeId: 'person',
  label: 'Person',
  icon: 'user',
  category: 'entity',
  colorToken: 'token-person',
  payloadSchema: z.object({
    name: z.string().min(1),
    role: z.string().optional(),
  }),
  renderers: {
    dot: ({ colorToken }) => (
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
    ),
    label: ({ title }) => <span className="text-xs">{title}</span>,
    detail: (props) => <EntityCard {...props} />,
  },
  defaultSize: { width: 200, height: 80 },
  allowedConnections: ['skill', 'project', 'publication', 'concept'],
});

// Skill node
registry.register({
  typeId: 'skill',
  label: 'Skill',
  icon: 'wrench',
  category: 'component',
  colorToken: 'token-skill',
  payloadSchema: z.object({
    name: z.string().min(1),
    level: z.enum(['basic', 'intermediate', 'advanced']).optional(),
  }),
  renderers: {
    dot: ({ colorToken }) => (
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
    ),
    label: ({ title }) => <span className="text-xs">{title}</span>,
    detail: (props) => <EntityCard {...props} />,
  },
  defaultSize: { width: 180, height: 60 },
  allowedConnections: ['person', 'project', 'concept'],
});

// Project node
registry.register({
  typeId: 'project',
  label: 'Project',
  icon: 'folder',
  category: 'content',
  colorToken: 'token-project',
  payloadSchema: z.object({
    name: z.string().min(1),
    stage: z.enum(['draft', 'active', 'completed']).optional(),
  }),
  renderers: {
    dot: ({ colorToken }) => (
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
    ),
    label: ({ title }) => <span className="text-xs">{title}</span>,
    detail: (props) => <EntityCard {...props} />,
  },
  defaultSize: { width: 200, height: 80 },
  allowedConnections: ['person', 'skill', 'publication'],
});

// Publication node
registry.register({
  typeId: 'publication',
  label: 'Publication',
  icon: 'file-text',
  category: 'content',
  colorToken: 'token-publication',
  payloadSchema: z.object({
    title: z.string().min(1),
    year: z.string().optional(),
  }),
  renderers: {
    dot: ({ colorToken }) => (
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
    ),
    label: ({ title }) => <span className="text-xs">{title}</span>,
    detail: (props) => <EntityCard {...props} />,
  },
  defaultSize: { width: 220, height: 80 },
  allowedConnections: ['person', 'project', 'concept'],
});

// Concept node
registry.register({
  typeId: 'concept',
  label: 'Concept',
  icon: 'lightbulb',
  category: 'entity',
  colorToken: 'token-concept',
  payloadSchema: z.object({
    name: z.string().min(1),
    description: z.string().optional(),
  }),
  renderers: {
    dot: ({ colorToken }) => (
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
    ),
    label: ({ title }) => <span className="text-xs">{title}</span>,
    detail: (props) => <EntityCard {...props} />,
  },
  defaultSize: { width: 180, height: 60 },
  allowedConnections: ['person', 'skill', 'project', 'publication'],
});

// Document node
registry.register({
  typeId: 'document',
  label: 'Document',
  icon: 'file',
  category: 'content',
  colorToken: 'token-document',
  payloadSchema: z.object({
    title: z.string().min(1),
    type: z.enum(['cv', 'resume', 'report', 'other']).optional(),
  }),
  renderers: {
    dot: ({ colorToken }) => (
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
    ),
    label: ({ title }) => <span className="text-xs">{title}</span>,
    detail: (props) => <EntityCard {...props} />,
  },
  defaultSize: { width: 200, height: 80 },
  allowedConnections: ['section', 'entry'],
});

// Section node
registry.register({
  typeId: 'section',
  label: 'Section',
  icon: 'list',
  category: 'content',
  colorToken: 'token-section',
  payloadSchema: z.object({
    title: z.string().min(1),
    order: z.number().optional(),
  }),
  renderers: {
    dot: ({ colorToken }) => (
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
    ),
    label: ({ title }) => <span className="text-xs">{title}</span>,
    detail: (props) => <EntityCard {...props} />,
  },
  defaultSize: { width: 180, height: 60 },
  allowedConnections: ['document', 'entry'],
});

// Entry node
registry.register({
  typeId: 'entry',
  label: 'Entry',
  icon: 'list-item',
  category: 'content',
  colorToken: 'token-entry',
  payloadSchema: z.object({
    title: z.string().min(1),
    date: z.string().optional(),
  }),
  renderers: {
    dot: ({ colorToken }) => (
      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: `var(--${colorToken})` }} />
    ),
    label: ({ title }) => <span className="text-xs">{title}</span>,
    detail: (props) => <EntityCard {...props} />,
  },
  defaultSize: { width: 160, height: 50 },
  allowedConnections: ['section'],
});
```

---

## 5. Styles (Terran Command)

No styles — registry is pure logic. CSS tokens defined in GRP-001-11 (xy-theme.css).

---

## 6. Definition of Done

```
[ ] schema/registry.ts exports registry singleton
[ ] registry.register() adds types to internal Map
[ ] registry.get(typeId) returns definition
[ ] registry.validatePayload() returns Zod SafeParseResult
[ ] registry.validatePayload() handles unknown type gracefully
[ ] registry.sanitizePayload() applies sanitizer if defined
[ ] registry.canConnect() checks allowedConnections
[ ] register-defaults.ts registers all 8 node types
[ ] No TypeScript errors
[ ] Schema step (GRP-001-02) now works with validation
```

---

## 7. E2E (TestSprite)

Test via integration in later steps:
1. Import registry in schemaToGraph
2. Pass valid node → validatePayload returns success: true
3. Pass invalid node → validatePayload returns success: false
4. Pass unknown type → validatePayload returns error
5. Test canConnect for valid/invalid connections

---

## 8. Git Workflow

### Commit

```
feat(registry): implement Node Type Registry (GRP-001-03)

- schema/registry.ts (NodeTypeRegistry class)
- schema/registry.types.ts (NodeTypeDefinition interface)
- schema/register-defaults.ts (8 default node types)
- Validation via Zod schemas
- Connection rules via allowedConnections
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-03: Node Type Registry with validation.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `zod` | Runtime validation (per Guide) |
| `dompurify` | Sanitization (per Guide, referenced but optional) |

**Note:** L3 components (EntityCard) are referenced in renderers but not created yet. Placeholder components or errors are acceptable until GRP-001-04.

---

## 10. Next Step

GRP-001-04 — L3 Content Components (EntityCard, PropertiesPreview, PropertyEditor, PlaceholderNode) — reusable components that the registry references.