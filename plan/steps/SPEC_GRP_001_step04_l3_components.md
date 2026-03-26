# Step 4: L3 Content Components

**Spec:** SPEC_GRP_001  
**Phase:** 3 (UI Components)  
**Priority:** HIGH — Registry references these in renderers  
**Dependency:** GRP-001-03 (registry must exist), UI-001-01 (shadcn components)

---

## 1. Migration Notes

> Not applicable — these are new L3 components. No legacy component to extract.

**Why this step exists:**
- Blueprint: "L3 — Content (Componentes reutilizables)"
- Current KnowledgeGraph.tsx has inline node rendering in `SimpleNodeCard` (lines 551-631)
- L3 components are reusable: work inside nodes, in Sheet panels, in tables
- Registry's `renderers.detail` points to these components

---

## 2. Data Contract

### EntityCard Props

```ts
interface EntityCardProps {
  title: string;                    // node name
  category: string;                 // node type
  properties?: Record<string, string>;  // key/value pairs
  badges?: string[];                // optional badges
  visualToken?: string;            // color reference
}
```

### PropertiesPreview Props

```ts
interface PropertiesPreviewProps {
  properties: Record<string, string>;  // read-only key/value pairs
}
```

### PropertyEditor Props

```ts
interface PropertyPair {
  key: string;
  value: string;
  dataType: AttributeType;
}

type AttributeType = 
  | "string" 
  | "text_markdown" 
  | "number" 
  | "date" 
  | "datetime" 
  | "boolean" 
  | "enum" 
  | "enum_open";

interface PropertyEditorProps {
  pairs: PropertyPair[];
  onChange: (pairs: PropertyPair[]) => void;
  readOnly?: boolean;
}
```

### PlaceholderNode Props

```ts
interface PlaceholderNodeProps {
  colorToken: string;  // CSS variable reference
}
```

---

## 3. Files to Create

```
apps/review-workbench/src/
├── components/content/
│   ├── EntityCard.tsx           # Title + category + badges + preview
│   ├── PropertiesPreview.tsx    # Collapsible key/value table (read-only)
│   ├── PropertyEditor.tsx       # Multi-type input fields (editable)
│   └── PlaceholderNode.tsx      # Skeleton for zoom-out
```

---

## 4. Implementation

### Required wiring step (from registry placeholders)

After creating L3 components, update registry detail renderers to replace Step 03 placeholders with real components. This is required to close the temporary anti-circular setup.

### components/content/EntityCard.tsx

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { EntityCardProps } from './types';

export function EntityCard({ title, category, properties, badges, visualToken }: EntityCardProps) {
  return (
    <Card 
      className="min-w-[200px]"
      style={{ borderLeftColor: visualToken ? `var(--${visualToken})` : undefined }}
    >
      <CardHeader className="p-3 pb-1">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          <Badge variant="outline" className="text-xs">{category}</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-1">
        {badges && badges.length > 0 && (
          <div className="flex gap-1 flex-wrap mb-2">
            {badges.map(badge => (
              <Badge key={badge} variant="secondary" className="text-[10px]">
                {badge}
              </Badge>
            ))}
          </div>
        )}
        {properties && Object.keys(properties).length > 0 && (
          <div className="text-xs text-muted-foreground">
            {Object.entries(properties).slice(0, 3).map(([k, v]) => (
              <div key={k} className="truncate">
                <span className="font-mono text-[10px]">{k}:</span>{" "}
                <span className="truncate">{v}</span>
              </div>
            ))}
            {Object.keys(properties).length > 3 && (
              <div className="text-[10px] text-muted">
                +{Object.keys(properties).length - 3} more
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### components/content/PropertiesPreview.tsx

```tsx
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { PropertiesPreviewProps } from './types';

export function PropertiesPreview({ properties }: PropertiesPreviewProps) {
  const entries = Object.entries(properties);
  if (entries.length === 0) return null;
  
  return (
    <Collapsible>
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="w-full justify-between font-mono text-[10px] uppercase">
          <span>Properties</span>
          <span className="text-xs text-muted-foreground">{entries.length}</span>
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px] text-xs">Key</TableHead>
              <TableHead className="text-xs">Value</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map(([key, value]) => (
              <TableRow key={key}>
                <TableCell className="font-mono text-xs py-1">{key}</TableCell>
                <TableCell className="text-xs py-1 truncate max-w-[200px]">{value}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CollapsibleContent>
    </Collapsible>
  );
}
```

### components/content/PropertyEditor.tsx

```tsx
import { useState } from 'react';
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import type { PropertyEditorProps, PropertyPair, AttributeType } from './types';

const ATTRIBUTE_TYPES: AttributeType[] = [
  "string", "text_markdown", "number", "date", "datetime", "boolean", "enum", "enum_open"
];

export function PropertyEditor({ pairs, onChange, readOnly = false }: PropertyEditorProps) {
  const updatePair = (index: number, updates: Partial<PropertyPair>) => {
    const newPairs = [...pairs];
    newPairs[index] = { ...newPairs[index], ...updates };
    onChange(newPairs);
  };
  
  const addPair = () => {
    onChange([...pairs, { key: "", value: "", dataType: "string" }]);
  };
  
  const removePair = (index: number) => {
    onChange(pairs.filter((_, i) => i !== index));
  };
  
  return (
    <div className="space-y-3">
      {pairs.map((pair, index) => (
        <div key={index} className="space-y-1">
          <div className="flex gap-1">
            <Input
              value={pair.key}
              onChange={(e) => updatePair(index, { key: e.target.value })}
              placeholder="key"
              className="font-mono text-xs h-8"
              disabled={readOnly}
            />
            <Select
              value={pair.dataType}
              onValueChange={(value: AttributeType) => updatePair(index, { dataType: value })}
              disabled={readOnly}
            >
              <SelectTrigger className="w-[100px] h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ATTRIBUTE_TYPES.map(type => (
                  <SelectItem key={type} value={type} className="text-xs">
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {!readOnly && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => removePair(index)}
                className="h-8 px-2 text-destructive"
              >
                ×
              </Button>
            )}
          </div>
          
          {renderValueInput(pair, (value) => updatePair(index, { value }), readOnly)}
        </div>
      ))}
      
      {!readOnly && (
        <Button variant="outline" size="sm" onClick={addPair} className="w-full">
          + Add Property
        </Button>
      )}
    </div>
  );
}

function renderValueInput(
  pair: PropertyPair, 
  onChange: (value: string) => void,
  readOnly: boolean
) {
  switch (pair.dataType) {
    case "text_markdown":
      return (
        <Textarea 
          value={pair.value} 
          onChange={(e) => onChange(e.target.value)} 
          placeholder="Markdown content..."
          className="min-h-[80px] text-xs"
          disabled={readOnly}
        />
      );
    
    case "number":
      return (
        <Input 
          type="number" 
          value={pair.value} 
          onChange={(e) => onChange(e.target.value)} 
          placeholder="0"
          className="text-xs"
          disabled={readOnly}
        />
      );
    
    case "date":
      return (
        <Input 
          type="date" 
          value={pair.value} 
          onChange={(e) => onChange(e.target.value)} 
          className="text-xs"
          disabled={readOnly}
        />
      );
    
    case "datetime":
      return (
        <Input 
          type="datetime-local" 
          value={pair.value} 
          onChange={(e) => onChange(e.target.value)} 
          className="text-xs"
          disabled={readOnly}
        />
      );
    
    case "boolean":
      return (
        <div className="flex items-center gap-2">
          <Checkbox 
            checked={pair.value === "true"} 
            onCheckedChange={(checked) => onChange(String(checked))}
            disabled={readOnly}
          />
          <span className="text-xs">{pair.value === "true" ? "true" : "false"}</span>
        </div>
      );
    
    case "enum":
      return (
        <Select value={pair.value} onValueChange={onChange} disabled={readOnly}>
          <SelectTrigger className="text-xs">
            <SelectValue placeholder="select..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="low" className="text-xs">Low</SelectItem>
            <SelectItem value="medium" className="text-xs">Medium</SelectItem>
            <SelectItem value="high" className="text-xs">High</SelectItem>
          </SelectContent>
        </Select>
      );
    
    default:
      return (
        <Input 
          value={pair.value} 
          onChange={(e) => onChange(e.target.value)} 
          placeholder={pair.dataType === "enum_open" ? "value (free enum)" : "value"}
          className="text-xs"
          disabled={readOnly}
        />
      );
  }
}
```

### components/content/PlaceholderNode.tsx

```tsx
import { Skeleton } from "@/components/ui/skeleton";
import type { PlaceholderNodeProps } from './types';

export function PlaceholderNode({ colorToken }: PlaceholderNodeProps) {
  return (
    <div 
      className="w-4 h-4 rounded-full"
      style={{ 
        backgroundColor: colorToken.includes('var(--') 
          ? colorToken 
          : `var(--${colorToken}, #888)` 
        }}
    />
  );
}

export function NodeSkeleton() {
  return (
    <div className="w-[180px] p-3 border border-border rounded-lg bg-card">
      <Skeleton className="h-4 w-3/4 mb-2" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  );
}

export function EdgeSkeleton() {
  return (
    <div className="flex items-center gap-2">
      <Skeleton className="h-2 w-2 rounded-full" />
      <Skeleton className="h-1 w-16" />
      <Skeleton className="h-2 w-2 rounded-full" />
    </div>
  );
}
```

### components/content/types.ts

```ts
// Type exports for L3 components

export interface EntityCardProps {
  title: string;
  category: string;
  properties?: Record<string, string>;
  badges?: string[];
  visualToken?: string;
}

export interface PropertiesPreviewProps {
  properties: Record<string, string>;
}

export interface PropertyPair {
  key: string;
  value: string;
  dataType: AttributeType;
}

export type AttributeType = 
  | "string" 
  | "text_markdown" 
  | "number" 
  | "date" 
  | "datetime" 
  | "boolean" 
  | "enum" 
  | "enum_open";

export interface PropertyEditorProps {
  pairs: PropertyPair[];
  onChange: (pairs: PropertyPair[]) => void;
  readOnly?: boolean;
}

export interface PlaceholderNodeProps {
  colorToken: string;
}
```

---

## 5. Styles (Terran Command)

Per Guide: "Background: bg-surface", "Headers: font-mono text-[10px] uppercase"
- Uses shadcn Card, Badge, Table components
- Consistent with existing app styling

---

## 6. Definition of Done

```
[ ] EntityCard renders title, category badge, properties preview
[ ] PropertiesPreview collapses/expands
[ ] PropertyEditor handles all 8 attribute types
[ ] PropertyEditor add/remove works
[ ] PlaceholderNode shows colored dot
[ ] NodeSkeleton shows loading state
[ ] Registry step (GRP-001-03) renderers now resolve to real components
[ ] No TypeScript errors
```

---

## 7. Local Verification

1. Render `EntityCard`, `PropertiesPreview`, and `PropertyEditor` in isolation.
2. Verify registry renderer mapping now points to real L3 components.
3. Confirm placeholders are no longer used for detail tier after wiring.
4. Typecheck touched modules.

---

## 8. Git Workflow

### Commit

```
feat(l3): implement L3 content components (GRP-001-04)

- components/content/EntityCard.tsx
- components/content/PropertiesPreview.tsx
- components/content/PropertyEditor.tsx (all 8 types)
- components/content/PlaceholderNode.tsx
- components/content/types.ts
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-04: L3 content components (EntityCard, PropertiesPreview, PropertyEditor, PlaceholderNode).
```

---

## 9. Dependencies

| Dep | Reason |
|-----|--------|
| `@/components/ui/card` | shadcn Card component |
| `@/components/ui/badge` | shadcn Badge component |
| `@/components/ui/table` | shadcn Table component |
| `@/components/ui/collapsible` | shadcn Collapsible component |
| `@/components/ui/input` | shadcn Input component |
| `@/components/ui/select` | shadcn Select component |
| `@/components/ui/checkbox` | shadcn Checkbox component |
| `@/components/ui/skeleton` | shadcn Skeleton component |

**Note:** UI-001-01 must be completed first to have these components installed.

---

## 10. Next Step

GRP-001-05 — GraphCanvas (ReactFlow wrapper) — renders the canvas with these L3 components inside nodes.
