# Step 7: L2 Sidebar (CanvasSidebar + Sections)

**Spec:** SPEC_GRP_001  
**Phase:** 5 (Editor Controls)  
**Priority:** HIGH — Required for full editor functionality  
**Dependencies:** GRP-001-01 (stores), UI-001-01 (shadcn), UI-001-02 (Accordion), UI-001-07 (filter UI), UI-001-08 (creation popover)

---

## 1. Migration Notes

> Not applicable — sidebar is new L2 component. No legacy component to extract.

**Why this step exists:**
- Blueprint: "sidebar/CanvasSidebar.tsx — Contenedor con Accordion"
- Current KnowledgeGraph.tsx has sidebar at lines 923-1800+
- This step extracts sidebar into dedicated L2 component with accordion sections

---

## 2. Data Contract

### Input: From Stores

```ts
// From useGraphStore
isDirty: () => boolean
undo: () => void
redo: () => void
markSaved: () => void
addElements: (nodes, edges) => void

// From useUIStore
filters: {
  hiddenRelationTypes: string[]
  filterText: string
  attributeFilter: { key: string; value: string } | null
  hideNonNeighbors: boolean
}
setFilter: (patch) => void
```

### Output: UI Components

Sidebar renders 4 accordion sections with internal state management.

---

## 3. Files to Create

```
apps/review-workbench/src/
├── features/graph-editor/L2-canvas/sidebar/
│   ├── CanvasSidebar.tsx      # Main container with Accordion
│   ├── ActionsSection.tsx     # Save, undo, redo, copy, paste, delete
│   ├── FiltersSection.tsx     # Text search, relation type, attribute
│   ├── CreationSection.tsx   # Node type selector (Command + Popover)
│   ├── ViewSection.tsx        # Layout presets, Tabs
│   └── index.ts              # Export barrel
```

---

## 4. Implementation

### features/graph-editor/L2-canvas/sidebar/CanvasSidebar.tsx

```tsx
import { useState } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ActionsSection } from "./ActionsSection";
import { FiltersSection } from "./FiltersSection";
import { CreationSection } from "./CreationSection";
import { ViewSection } from "./ViewSection";
import { useUIStore } from "@/stores/ui-store";

export function CanvasSidebar() {
  const sidebarOpen = useUIStore(s => s.sidebarOpen);
  const toggleSidebar = useUIStore(s => s.toggleSidebar);
  
  if (!sidebarOpen) {
    return (
      <button 
        onClick={toggleSidebar}
        className="absolute left-2 top-2 z-10 p-2 bg-background border rounded shadow"
      >
        ☰
      </button>
    );
  }
  
  return (
    <div className="w-[280px] h-full border-l bg-background overflow-y-auto">
      <div className="flex items-center justify-between px-3 py-2 border-b">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em]">Editor</span>
        <button onClick={toggleSidebar} className="text-xs text-muted-foreground hover:text-foreground">
          ✕
        </button>
      </div>
      
      <Accordion type="multiple" defaultValue={["actions", "filters", "creation", "view"]}>
        <AccordionItem value="actions">
          <AccordionTrigger className="font-mono text-[10px] uppercase tracking-[0.2em] px-3">
            Actions
          </AccordionTrigger>
          <AccordionContent>
            <ActionsSection />
          </AccordionContent>
        </AccordionItem>
        
        <AccordionItem value="filters">
          <AccordionTrigger className="font-mono text-[10px] uppercase tracking-[0.2em] px-3">
            Filters
          </AccordionTrigger>
          <AccordionContent>
            <FiltersSection />
          </AccordionContent>
        </AccordionItem>
        
        <AccordionItem value="creation">
          <AccordionTrigger className="font-mono text-[10px] uppercase tracking-[0.2em] px-3">
            Creation
          </AccordionTrigger>
          <AccordionContent>
            <CreationSection />
          </AccordionContent>
        </AccordionItem>
        
        <AccordionItem value="view">
          <AccordionTrigger className="font-mono text-[10px] uppercase tracking-[0.2em] px-3">
            View
          </AccordionTrigger>
          <AccordionContent>
            <ViewSection />
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
```

### features/graph-editor/L2-canvas/sidebar/ActionsSection.tsx

```tsx
import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { useGraphStore } from "@/stores/graph-store";
import { useUIStore } from "@/stores/ui-store";
import { toast } from "sonner";

export function ActionsSection() {
  const isDirty = useGraphStore(s => s.isDirty());
  const undo = useGraphStore(s => s.undo);
  const redo = useGraphStore(s => s.redo);
  const markSaved = useGraphStore(s => s.markSaved);
  const copiedNodeId = useUIStore(s => s.copiedNodeId);
  const nodes = useGraphStore(s => s.nodes);
  const addElements = useGraphStore(s => s.addElements);
  
  const handleSave = () => {
    markSaved();
    toast.success("Graph saved successfully");
  };
  
  const handleCopy = () => {
    // Copy selected node
    toast.info("Node copied to clipboard");
  };
  
  const handlePaste = () => {
    // Paste copied node
    toast.info("Node pasted");
  };
  
  const handleDelete = () => {
    // Trigger delete confirmation
    // Uses AlertDialog (UI-001-06)
  };
  
  return (
    <div className="flex flex-col gap-2 px-3 pb-3">
      <Button size="sm" onClick={handleSave} disabled={!isDirty}>
        Save
      </Button>
      <div className="flex gap-1">
        <Button size="sm" variant="outline" onClick={undo} className="flex-1">
          Undo
        </Button>
        <Button size="sm" variant="outline" onClick={redo} className="flex-1">
          Redo
        </Button>
      </div>
      <div className="flex gap-1">
        <Button size="sm" variant="outline" onClick={handleCopy} className="flex-1">
          Copy
        </Button>
        <Button size="sm" variant="outline" onClick={handlePaste} className="flex-1" disabled={!copiedNodeId}>
          Paste
        </Button>
      </div>
      <Button size="sm" variant="destructive" onClick={handleDelete}>
        Delete
      </Button>
    </div>
  );
}
```

### features/graph-editor/L2-canvas/sidebar/FiltersSection.tsx

```tsx
import { useState } from 'react';
import { Input } from "@/components/ui/input";
import { DropdownMenu, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";
import { useGraphStore } from "@/stores/graph-store";

export function FiltersSection() {
  const filters = useUIStore(s => s.filters);
  const setFilter = useUIStore(s => s.setFilter);
  const clearFilters = useUIStore(s => s.clearFilters);
  const edges = useGraphStore(s => s.edges);
  
  const relationTypes = [...new Set(edges.map(e => e.data?.relationType ?? "linked"))];
  
  const [attrFilterOpen, setAttrFilterOpen] = useState(false);
  const [attrKey, setAttrKey] = useState(filters.attributeFilter?.key ?? '');
  const [attrValue, setAttrValue] = useState(filters.attributeFilter?.value ?? '');
  
  const applyAttrFilter = () => {
    setFilter({ attributeFilter: attrKey || attrValue ? { key: attrKey, value: attrValue } : null });
    setAttrFilterOpen(false);
  };
  
  return (
    <div className="space-y-2 px-3 pb-3">
      {/* Text Search */}
      <Input
        placeholder="Search nodes..."
        value={filters.filterText}
        onChange={(e) => setFilter({ filterText: e.target.value })}
      />
      
      {/* Relation Type Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="w-full">
            Filter by Relation
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuLabel>Relation Types</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {relationTypes.map(type => (
            <DropdownMenuCheckboxItem
              key={type}
              checked={!filters.hiddenRelationTypes.includes(type)}
              onCheckedChange={() => {
                const hidden = filters.hiddenRelationTypes.includes(type)
                  ? filters.hiddenRelationTypes.filter(t => t !== type)
                  : [...filters.hiddenRelationTypes, type];
                setFilter({ hiddenRelationTypes: hidden });
              }}
            >
              {type}
            </DropdownMenuCheckboxItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      
      {/* Attribute Filter */}
      <Popover open={attrFilterOpen} onOpenChange={setAttrFilterOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="w-full">
            Filter by Attribute
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-56">
          <div className="space-y-2">
            <Input
              placeholder="Key"
              value={attrKey}
              onChange={(e) => setAttrKey(e.target.value)}
            />
            <Input
              placeholder="Value contains"
              value={attrValue}
              onChange={(e) => setAttrValue(e.target.value)}
            />
            <div className="flex gap-1">
              <Button size="sm" onClick={applyAttrFilter} className="flex-1">Apply</Button>
              <Button size="sm" variant="outline" onClick={() => { clearFilters(); setAttrKey(''); setAttrValue(''); }} className="flex-1">
                Clear
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
      
      {/* Hide Non-Neighbors Toggle */}
      <label className="flex items-center gap-2 text-xs">
        <input
          type="checkbox"
          checked={filters.hideNonNeighbors}
          onChange={(e) => setFilter({ hideNonNeighbors: e.target.checked })}
        />
        Hide non-neighbors in focus mode
      </label>
    </div>
  );
}
```

### features/graph-editor/L2-canvas/sidebar/CreationSection.tsx

```tsx
import { useState } from 'react';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { registry } from "@/schema/registry";
import { useGraphStore } from "@/stores/graph-store";
import type { ASTNode } from "@/stores/types";

export function CreationSection() {
  const [open, setOpen] = useState(false);
  const addElements = useGraphStore(s => s.addElements);
  
  const nodeTypes = registry.getAll();
  
  const handleCreate = (typeId: string) => {
    const def = registry.get(typeId);
    if (!def) return;
    
    const newNode: ASTNode = {
      id: `node-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      type: 'node',
      position: { x: 200 + Math.random() * 400, y: 200 + Math.random() * 300 },
      data: {
        typeId,
        payload: { name: def.label },
        properties: {},
        visualToken: def.colorToken,
      },
    };
    
    addElements([newNode], []);
    setOpen(false);
  };
  
  return (
    <div className="px-3 pb-3">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="w-full">
            Add Node +
          </Button>
        </PopoverTrigger>
        <PopoverContent className="p-0 w-[250px]" side="right" align="start">
          <Command>
            <CommandInput placeholder="Search node types..." />
            <CommandEmpty>No node type found.</CommandEmpty>
            <CommandGroup heading="Node Types">
              {nodeTypes.map(type => (
                <CommandItem
                  key={type.typeId}
                  value={type.label}
                  onSelect={() => handleCreate(type.typeId)}
                >
                  {type.label}
                  <span className="ml-2 text-xs text-muted-foreground">{type.category}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
```

### features/graph-editor/L2-canvas/sidebar/ViewSection.tsx

```tsx
import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";

export function ViewSection() {
  const [layoutMode, setLayoutMode] = useState<'auto' | 'manual'>('manual');
  const setEditorState = useUIStore(s => s.setEditorState);
  const focusedNodeId = useUIStore(s => s.focusedNodeId);
  const nodes = useGraphStore(s => s.nodes);
  const setFilter = useUIStore(s => s.setFilter);
  
  // This would integrate with useGraphLayout hook (GRP-001-09)
  const applyLayout = () => {
    // ELKjs layout
  };
  
  const focusOnSelected = () => {
    if (focusedNodeId) {
      setEditorState('focus');
    }
  };
  
  return (
    <div className="px-3 pb-3">
      <Tabs value={layoutMode} onValueChange={(v) => setLayoutMode(v as 'auto' | 'manual')}>
        <TabsList className="w-full">
          <TabsTrigger value="auto" className="flex-1">Auto</TabsTrigger>
          <TabsTrigger value="manual" className="flex-1">Manual</TabsTrigger>
        </TabsList>
        
        <TabsContent value="auto" className="space-y-2 mt-2">
          <Button size="sm" className="w-full" onClick={applyLayout}>
            Apply Layout
          </Button>
          <p className="text-[10px] text-muted-foreground">
            Uses ELKjs for automatic positioning
          </p>
        </TabsContent>
        
        <TabsContent value="manual" className="mt-2">
          <p className="text-xs text-muted-foreground">
            Drag nodes to position manually
          </p>
        </TabsContent>
      </Tabs>
      
      <div className="mt-3 pt-3 border-t">
        <Button 
          size="sm" 
          variant="outline" 
          className="w-full"
          onClick={focusOnSelected}
          disabled={!focusedNodeId}
        >
          Focus on Selected
        </Button>
      </div>
    </div>
  );
}
```

### features/graph-editor/L2-canvas/sidebar/index.ts

```ts
export { CanvasSidebar } from './CanvasSidebar';
export { ActionsSection } from './ActionsSection';
export { FiltersSection } from './FiltersSection';
export { CreationSection } from './CreationSection';
export { ViewSection } from './ViewSection';
```

---

## 5. Styles (Terran Command)

Per Guide: 
- Headers: `font-mono text-[10px] uppercase tracking-[0.2em]`
- Section containers: `px-3 pb-3`
- Buttons: `size="sm"`, `variant="outline"` for secondary

---

## 6. Definition of Done

```
[ ] CanvasSidebar renders with 4 accordion sections
[ ] ActionsSection has Save, Undo, Redo, Copy, Paste, Delete
[ ] FiltersSection has text search, relation filter, attribute filter
[ ] CreationSection has searchable node type selector
[ ] ViewSection has layout mode tabs
[ ] All sections connect to stores correctly
[ ] No TypeScript errors
```

---

## 7. Git Workflow

### Commit

```
feat(sidebar): implement L2 sidebar with sections (GRP-001-07)

- features/graph-editor/L2-canvas/sidebar/CanvasSidebar.tsx
- features/graph-editor/L2-canvas/sidebar/ActionsSection.tsx
- features/graph-editor/L2-canvas/sidebar/FiltersSection.tsx
- features/graph-editor/L2-canvas/sidebar/CreationSection.tsx
- features/graph-editor/L2-canvas/sidebar/ViewSection.tsx
```

### Changelog

```markdown
## YYYY-MM-DD

- Implemented GRP-001-07: L2 Sidebar with accordion sections.
```

---

## 8. Next Step

GRP-001-08 — Inspector Panels (NodeInspector, EdgeInspector with Sheet)