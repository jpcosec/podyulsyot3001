# Component Map — Terran Command UI

> **START HERE** - Define qué componentes existen y cómo se comunican.

---

## Capas de Componentes

| Capa | Descripción | Ubicación |
|-------|-------------|-----------|
| **Foundation** | Átomos y moléculas base | `_foundation/` |
| **L1** | Vistas y páginas (orquestación) | `01_L1_ui_app/` |
| **L2** | Graph Canvas (motor espacial) | `02_L2_graph_viewer/` |
| **L3** | Internal Nodes (contenido) | `03_L3_internal_nodes/` |

---

## Arquitectura de Capas

```
┌─────────────────────────────────────────────────────────────┐
│ L1: 01_L1_ui_app (Vistas / Pages)                          │
│   ├── PortfolioDashboard (A1)                               │
│   ├── DataExplorer (A2)                                    │
│   ├── BaseCvEditor (A3)                                   │
│   └── JobFlowInspector / B1-B5 (Jobs)                       │
│       ↓ Props: ASTNode[], ASTEdge[], themeTokens           │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ L2: 02_L2_graph_viewer (Graph Canvas)                       │
│   ├── UniversalGraphCanvas                                 │
│   ├── UniversalNodeShell                                   │
│   ├── UniversalGroupShell                                  │
│   └── ProxyEdge                                           │
│       ↓ Payload: contentType, contentData                 │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ L3: 03_L3_internal_nodes (Contenido)                        │
│   ├── InternalNodeRouter                                   │
│   ├── IntelligentEditor (modos: fold/tag-hover/diff)      │
│   ├── JsonPreview                                          │
│   └── ...                                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ _foundation (UI Base)                                      │
│   ├── Átomos: Button, Badge, Tag, Icon, Spinner, Kbd    │
│   └── Moléculas: SplitPane, ControlPanel, DiagnosticCard │
└─────────────────────────────────────────────────────────────┘
```

---

## Contratos de Comunicación

### L1 → L2 (App → Graph Canvas)

```typescript
// Props que L1 le pasa a L2
interface AppToCanvasProps {
  nodes: ASTNode[];
  edges: ASTEdge[];
  themeTokens: Record<string, StyleToken>;
  isReadOnly?: boolean;
  layoutEngine?: 'dagre' | 'manual';
}

// Eventos que L2 emite hacia L1
interface CanvasToAppEvents {
  onNodeClick: (nodeId: string, attributes: Record<string, any>) => void;
  onEdgeClick: (edgeId: string) => void;
  onTopologyMutate: (newAST: AST) => void;
}
```

### L2 → L3 (Graph Canvas → Node)

```typescript
// Props que L2 le pasa a cada nodo
interface CanvasToNodeProps {
  nodeId: string;
  isFocused: boolean;
  payload: NodePayload;
  themeToken: StyleToken;
}

// Eventos que L3 emite hacia L2
interface NodeToCanvasEvents {
  onContentMutate: (nodeId: string, newPayload: any) => void;
  onRequestFocus: (nodeId: string) => void;
}
```

---

## Componentes por Capa

### Foundation (`_foundation/`)

| Componente | Tipo | Descripción |
|------------|------|-------------|
| `Button` | Átomo | variant: primary/ghost/danger, size: sm/md |
| `Badge` | Átomo | variant: primary/secondary/success/muted |
| `Tag` | Átomo | category: skill/req/risk, onHover, onClick |
| `Icon` | Átomo | Lucide wrapper, size: xs/sm/md |
| `Spinner` | Átomo | Loading indicator |
| `Kbd` | Átomo | Keyboard shortcuts |
| `SplitPane` | Molécula | react-resizable-panels wrapper |
| `ControlPanel` | Molécula | Generic panel with actions |
| `DiagnosticCard` | Molécula | Card with status |

### L1: UI App (`01_L1_ui_app/`)

| Componente | Spec | Layout | Dependencias |
|------------|------|--------|--------------|
| `PortfolioDashboard` | A1 | Grid 9/3 | Table, Progress |
| `DataExplorer` | A2 | SplitPane 30/70 | IntelligentEditor, FileTree |
| `BaseCvEditor` | A3 | Grid 70/30 | GraphCanvas, NodeInspector |
| `JobFlowInspector` | B0 | Columna | PipelineTimeline |
| `ScrapeDiagnostics` | B1 | Columna | DiagnosticCard |
| `ExtractUnderstand` | B2 | SplitPane 50/50 | IntelligentEditor, RequirementList |
| `Match` | B3 | SplitPane 3col | GraphCanvas, EvidenceBank |
| `GenerateDocuments` | B4 | SplitPane 50/50 | IntelligentEditor, DocumentTabs |
| `PackageDeployment` | B5 | SplitPane | PackageFileList |

### L2: Graph Viewer (`02_L2_graph_viewer/`)

| Componente | Descripción |
|------------|-------------|
| `UniversalGraphCanvas` | Wrapper de ReactFlow + Background + Controls |
| `UniversalNodeShell` | Cascarón visual para nodos simples |
| `UniversalGroupShell` | Cascarón para grupos colapsables |
| `ProxyEdge` | Edge custom para conexiones cruzadas |
| `LayoutEngine` | Dagre/ELK para auto-layout |

### L3: Internal Nodes (`03_L3_internal_nodes/`)

| Componente | contentType | Descripción |
|------------|-------------|-------------|
| `InternalNodeRouter` | - | Switch que renderiza según contentType |
| `IntelligentEditor` | markdown, tags | Editor con tags interactivos |
| `JsonPreview` | json | Visor de JSON con syntax highlighting |
| `PropertyList` | property_list | Lista de atributos key-value |
| `ImagePreview` | image | Visor de imágenes |
| `EmptyNode` | empty | Nodo sin contenido (grupos colapsados) |

---

## Modos de IntelligentEditor

| Modo | Vista | Comportamiento |
|------|-------|----------------|
| `fold` | A2 Data Explorer | Solo renderiza texto, sin tags |
| `tag-hover` | B2 Extract | Tags interactivos, hover muestra card |
| `diff` | B4 Generate Docs | Diff entre versión anterior y nueva |

---

## Docs por Capa

```
plan/
├── 00_component_map.md           ← Este archivo
├── _foundation/
│   └── atoms_molecules.md        # Definición de UI base
├── 01_L1_ui_app/
│   └── views.md                  # Pages y layouts
├── 02_L2_graph_viewer/
│   └── graph_canvas.md          # Componentes del canvas
└── 03_L3_internal_nodes/
    └── internal_nodes.md         # Contenido de nodos
```

---

## Archivo Target

```
src/
├── components/
│   ├── atoms/                    # _foundation
│   ├── molecules/                 # _foundation
│   ├── layouts/                   # _foundation
│   ├── organisms/                 # L2 + L3
│   └── GraphCanvas/              # L2 (nuevo)
├── features/                     # L1 (Feature-Sliced)
├── pages/                        # L1
└── ...
```
