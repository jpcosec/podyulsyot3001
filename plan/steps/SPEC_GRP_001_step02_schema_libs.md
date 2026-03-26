# Step 2: Schema Translation (schemaToGraph / graphToDomain)

**Spec:** SPEC_GRP_001  
**Phase:** 1 (Data Foundation)  
**Priority:** HIGH — All UI steps depend on having real data to render  
**Dependency:** GRP-001-01 (stores/types.ts must be created first)

---

## 1. Migration Notes

> Not applicable — this is new code. No legacy component to extract.

**Why this step exists:**
- Blueprint mandates schema → AST translation (per Guide: "Motor schemaToGraph()" is in 01_L1_ui_app/)
- Current KnowledgeGraph.tsx has hardcoded mock data in `buildInitialGraph()`
- We need a pipeline that: (1) reads raw API data → (2) validates against registry → (3) outputs AST → (4) renders UI

**Contract rule:** Keep payload contract aligned with `stores/types.ts` and registry runtime validation. Do not introduce a separate payload shape here.

---

## 2. Data Contract

### Input: Raw API Data

```ts
interface RawNode {
  id: string;
  type: string;           // e.g., "person", "skill", "project"
  name: string;
  properties: Record<string, string>;
  children?: RawNode[];  // hierarchical data
}

interface RawEdge {
  id: string;
  source: string;
  target: string;
  relationType: string;  // e.g., "uses", "owns", "knows"
  properties?: Record<string, string>;
}

interface RawData {
  nodes: RawNode[];
  edges: RawEdge[];
}
```

### Output: Validated AST

```ts
interface ASTNode {
  id: string;
  type: 'node' | 'error';  // 'error' if validation failed
  position: { x: number; y: number };
  data: {
    typeId: string;
    payload: NodePayload;
    properties: Record<string, string>;
    visualToken?: string;  // references xy-theme.css token
  };
  parentId?: string;
  hidden?: boolean;
}

interface ASTEdge {
  id: string;
  source: string;
  target: string;
  type: 'floating' | 'button';
  data?: {
    relationType: string;
    properties: Record<string, string>;
    _originalSource?: string;  // for edge inheritance
    _originalTarget?: string;
  };
  hidden?: boolean;
}

interface ValidationError {
  nodeId: string;
  message: string;
}

interface ValidatedAST {
  nodes: ASTNode[];
  edges: ASTEdge[];
  errors: ValidationError[];  // non-fatal, render as ErrorNode
}
```

### Output: Domain (for API)

```ts
interface DomainData {
  nodes: {
    id: string;
    type: string;
    name: string;
    properties: Record<string, string>;
    children: DomainNode[];  // nested
  }[];
  edges: {
    id: string;
    source: string;
    target: string;
    relationType: string;
    properties: Record<string, string>;
  }[];
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/
│   ├── lib/
│   │   ├── schema-to-graph.ts   # Raw → AST (with validation)
│   │   ├── graph-to-domain.ts   # AST → Domain (for API)
│   │   └── types.ts             # Local types (RawNode, RawData, etc.)
```

---

## 4. Implementation

### features/graph-editor/lib/types.ts

```ts
// Raw data types (from API)

export interface RawNode {
  id: string;
  type: string;
  name: string;
  properties: Record<string, string>;
  children?: RawNode[];
}

export interface RawEdge {
  id: string;
  source: string;
  target: string;
  relationType: string;
  properties?: Record<string, string>;
}

export interface RawData {
  nodes: RawNode[];
  edges: RawEdge[];
}

// Re-export AST types from stores
export type { ASTNode, ASTEdge, ValidationError, ValidatedAST } from '@/stores/types';

// Domain types (for API)
export interface DomainNode {
  id: string;
  type: string;
  name: string;
  properties: Record<string, string>;
  children: DomainNode[];
}

export interface DomainEdge {
  id: string;
  source: string;
  target: string;
  relationType: string;
  properties: Record<string, string>;
}

export interface DomainData {
  nodes: DomainNode[];
  edges: DomainEdge[];
}
```

### features/graph-editor/lib/schema-to-graph.ts

```ts
import type { RawNode, RawEdge, RawData, ASTNode, ASTEdge, ValidationError, ValidatedAST } from './types';
import { registry } from '@/schema/registry';

/**
 * Phase 1: Match raw nodes against registry, validate, sanitize
 */
function matchNodes(rawData: RawData): Map<string, ASTNode> {
  const nodeMap = new Map<string, ASTNode>();
  
  const processNode = (rawNode: RawNode, parentId?: string, depth = 0) => {
    const def = registry.get(rawNode.type);
    
    // Unknown type → ErrorNode (non-fatal)
    if (!def) {
      nodeMap.set(rawNode.id, {
        id: rawNode.id,
        type: 'error',
        position: { x: depth * 200, y: 0 },
        data: {
          typeId: 'error',
          payload: { message: `Unknown node type: ${rawNode.type}` },
          properties: rawNode.properties,
        },
        parentId,
      });
      return;
    }
    
    // Validate payload against Zod schema
    const validation = def.payloadSchema.safeParse({
      name: rawNode.name,
      ...rawNode.properties,
    });
    
    // Validation failed → ErrorNode (non-fatal)
    if (!validation.success) {
      nodeMap.set(rawNode.id, {
        id: rawNode.id,
        type: 'error',
        position: { x: depth * 200, y: 0 },
        data: {
          typeId: 'error',
          payload: { message: `Validation failed: ${validation.error.message}` },
          properties: rawNode.properties,
        },
        parentId,
      });
      return;
    }
    
    // Sanitize payload (DOMPurify or custom)
    const sanitized = def.sanitizer 
      ? def.sanitizer(validation.data) 
      : validation.data;
    
    const astNode: ASTNode = {
      id: rawNode.id,
      type: 'node',
      position: { x: depth * 200, y: 0 }, // Layout will reposition
      data: {
        typeId: rawNode.type,
        payload: {
          typeId: rawNode.type,
          value: sanitized,
        },
        properties: rawNode.properties,
        visualToken: def.colorToken,
      },
      parentId,
    };
    
    nodeMap.set(rawNode.id, astNode);
    
    // Process children recursively
    rawNode.children?.forEach(child => processNode(child, rawNode.id, depth + 1));
  };
  
  rawData.nodes.forEach(node => processNode(node));
  
  return nodeMap;
}

/**
 * Phase 2: Resolve edges (connect nodes)
 */
function resolveEdges(rawData: RawData, nodeMap: Map<string, ASTNode>): ASTEdge[] {
  const edges: ASTEdge[] = [];
  
  rawData.edges.forEach(rawEdge => {
    const sourceNode = nodeMap.get(rawEdge.source);
    const targetNode = nodeMap.get(rawEdge.target);
    
    // Skip edges to non-existent nodes
    if (!sourceNode || !targetNode) {
      return;
    }
    
    edges.push({
      id: rawEdge.id,
      source: rawEdge.source,
      target: rawEdge.target,
      type: 'floating',
      data: {
        relationType: rawEdge.relationType,
        properties: rawEdge.properties ?? {},
      },
    });
  });
  
  return edges;
}

/**
 * Main pipeline: Raw API data → Validated AST
 */
export function schemaToGraph(rawData: RawData): ValidatedAST {
  const nodeMap = matchNodes(rawData);
  const edges = resolveEdges(rawData, nodeMap);
  
  const errors: ValidationError[] = [];
  nodeMap.forEach((node, id) => {
    if (node.type === 'error') {
      errors.push({ nodeId: id, message: node.data.payload.message as string });
    }
  });
  
  return {
    nodes: Array.from(nodeMap.values()),
    edges,
    errors,
  };
}
```

### features/graph-editor/lib/graph-to-domain.ts

```ts
import type { ASTNode, ASTEdge, DomainData, DomainNode, DomainEdge } from './types';

/**
 * Converts AST back to domain format for API serialization
 * (inverse of schemaToGraph)
 */
export function graphToDomain(nodes: ASTNode[], edges: ASTEdge[]): DomainData {
  const rootNodes: DomainNode[] = [];
  const nodeById = new Map<string, DomainNode>();
  
  // Build hierarchical node structure
  nodes.forEach(node => {
    if (node.type === 'error') return; // Skip error nodes
    
    const domainNode: DomainNode = {
      id: node.id,
      type: node.data.typeId,
      name: (node.data.payload.name ?? node.data.payload.title ?? 'Untitled') as string,
      properties: node.data.properties,
      children: [],
    };
    
    nodeById.set(node.id, domainNode);
    
    if (node.parentId) {
      const parent = nodeById.get(node.parentId);
      if (parent) {
        parent.children.push(domainNode);
      }
    } else {
      rootNodes.push(domainNode);
    }
  });
  
  // Convert edges
  const domainEdges: DomainEdge[] = edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    relationType: edge.data?.relationType ?? 'linked',
    properties: edge.data?.properties ?? {},
  }));
  
  return {
    nodes: rootNodes,
    edges: domainEdges,
  };
}
```

---

## 5. Styles (Terran Command)

No styles — this is pure data transformation logic.

---

## 6. Definition of Done

```
[ ] features/graph-editor/lib/types.ts exports RawNode, RawData, DomainData
[ ] schemaToGraph() returns { nodes, edges, errors }
[ ] Unknown node type → ErrorNode (not crash)
[ ] Validation failure → ErrorNode (not crash)
[ ] Valid nodes have correct typeId, payload, visualToken
[ ] Children set parentId correctly
[ ] Edges reference existing nodes
[ ] graphToDomain() produces hierarchical structure
[ ] graphToDomain() produces flat edge array
[ ] No TypeScript errors
```

---

## 7. Local Verification

1. Pass valid raw data into `schemaToGraph()` and verify `nodes/edges/errors` shape.
2. Pass unknown type and verify `ErrorNode` is emitted (no crash).
3. Pass invalid payload and verify validation failure is captured in `errors`.
4. Run `graphToDomain()` and verify hierarchy + relation roundtrip.

---

## 8. Git Workflow

### Commit

```
feat(schema): implement schema translation (GRP-001-02)

- features/graph-editor/lib/types.ts
- features/graph-editor/lib/schema-to-graph.ts (raw → AST)
- features/graph-editor/lib/graph-to-domain.ts (AST → domain)
- Validation errors produce ErrorNode (non-fatal)
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-02: Schema translation pipeline.
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/stores/types` | Re-exports ASTNode, ASTEdge |
| `@/schema/registry` | Validates node payloads against Zod schemas |

**Note:** Registry (GRP-001-03) isn't created yet, but this step's code will fail until it's done. Step 3 must run immediately after.

---

## 10. Next Step

GRP-001-03 — Node Registry (type definitions, validation, allowed connections) — required for schemaToGraph to work.
