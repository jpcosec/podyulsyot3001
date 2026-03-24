# L1: Vistas y Páginas

> Orquestación, fetching, layout de pantalla. No sabe de ReactFlow.

---

## Vistas

| Spec | Vista | Layout | Main Component | Secondary |
|------|-------|--------|----------------|-----------|
| A1 | Portfolio Dashboard | Grid 9/3 | PortfolioTable, ProgressSegmented | DeadlineSensors, SystemStats |
| A2 | Data Explorer | SplitPane 30/70 | IntelligentEditor (fold) | FileTree |
| A3 | Base CV Editor | Grid 70/30 | **GraphCanvas** | NodeInspectorSidebar |
| B0 | Job Flow Inspector | Columna | PipelineTimeline, HitlCtaBanner | — |
| B1 | Scrape Diagnostics | Columna + Control | DiagnosticCard, ImagePreview | ScrapeControlPanel |
| B2 | Extract & Understand | SplitPane 50/50 | IntelligentEditor (tag-hover), RequirementList | ExtractControlPanel |
| B3 | Match | SplitPane 3 col | **GraphCanvas** | EvidenceBankSidebar, MatchControlPanel |
| B4 | Generate Documents | SplitPane 50/50 | IntelligentEditor (diff), DocumentTabs | PackageControlPanel |
| B5 | Package Deployment | SplitPane | MissionSummary, PackageFileList | DeploymentCta |

---

## Responsabilidades

- **Fetching** - Llama a APIs o mock
- **Layout** - Orchestrates componentes
- **Estado global** - Sidebar, filtros, selección
- **Persistencia** - Guardar cambios al backend
- **NO conoce ReactFlow** - Solo pasa props a L2

---

## Contrato L1 → L2

```typescript
interface L1ToL2Props {
  nodes: ASTNode[];
  edges: ASTEdge[];
  themeTokens: Record<string, StyleToken>;
  isReadOnly?: boolean;
  layoutEngine?: 'dagre' | 'manual';
}

interface L2ToL1Events {
  onNodeClick: (nodeId: string, attributes: Record<string, any>) => void;
  onEdgeClick: (edgeId: string) => void;
  onTopologyMutate: (newAST: AST) => void;
}
```

---

## Ejemplo: BaseCvEditor (A3)

```typescript
export function BaseCvEditor() {
  const { data } = useQuery(['cv-graph'], fetchCvGraph);
  const { astNodes, astEdges } = useMemo(() => schemaToGraph(data, cvSchema), [data]);

  return (
    <div className="grid grid-cols-[1fr_320px]">
      <UniversalGraphCanvas
        nodes={astNodes}
        edges={astEdges}
        onNodeClick={setSelectedNode}
      />
      <NodeInspectorSidebar nodeId={selectedNode} />
    </div>
  );
}
```

**Nota:** L1 no importa `@xyflow/react` directamente - solo pasa datos.
