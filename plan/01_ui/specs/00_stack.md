# Stack & Libraries — Terran Command UI

---

## Vistas → Librerías

| Spec | Vista | Layout | Componentes Core | Librerías |
|------|-------|--------|-----------------|-----------|
| A1 | Portfolio Dashboard | Grid 9/3 | `<PortfolioTable>` `<ProgressSegmented>` | `react-router-dom` · `@tanstack/react-query` |
| A2 | Data Explorer | `<SplitPane>` | `<IntelligentEditor>` `<FileTree>` | `react-resizable-panels` · `lucide-react` |
| A3 | Base CV Editor | Grid 70/30 | `<GraphCanvas>` `<NodeInspectorSidebar>` | `@xyflow/react` · `dagre` |
| B0 | Job Flow Inspector | Columna única | `<PipelineTimeline>` `<HitlCtaBanner>` | `@tanstack/react-query` (polling) |
| B1 | Scrape Diagnostics | Columna + Control | `<DiagnosticCard>` `<ImagePreview>` | Nativas React/Tailwind |
| B2 | Extract & Understand | `<SplitPane>` | `<IntelligentEditor>` `<RequirementList>` | `react-resizable-panels` · `@uiw/react-codemirror` |
| B3 | Match | `<SplitPane>` | `<GraphCanvas>` `<EvidenceBankSidebar>` | `@xyflow/react` · `@dnd-kit/core` |
| B4 | Generate Documents | `<SplitPane>` | `<IntelligentEditor>` `<DocumentTabs>` | `react-resizable-panels` · `@uiw/react-codemirror` (diff) |

---

## Moléculas → Motor

| Molécula | Átomos | Librería motor | Por qué |
|----------|--------|---------------|---------|
| `<SplitPane>` | — | `react-resizable-panels` | Del equipo core de React. Maneja divisores arrastrables, snap y collapse con Tailwind sin escribir cálculos de mouse. |
| `<IntelligentEditor>` | `<Tag>` `<Badge>` | `@uiw/react-codemirror` | Wrapper limpio de CodeMirror 6. Trae folding de JSON/MD, temas oscuros y sistema de decoraciones (tags) listo para usar. Reemplaza Slate.js. |
| `<GraphCanvas>` | `<Badge>` `<Icon>` | `@xyflow/react` + `dagre` | Ya en el proyecto. `dagre` calcula el layout jerárquico automático — los nodos no nacen amontonados. |
| `<EvidenceBankSidebar>` | `<Badge>` `<Icon>` | `@dnd-kit/core` | Estándar moderno para D&D en React. Permite arrastrar tarjetas del sidebar al canvas del grafo sin pelear con la API nativa de HTML5. |
| `<PortfolioTable>` | `<Badge>` `<Icon>` | `@tanstack/react-table` (opcional) | Si la tabla crece, maneja ordenamiento, filtros y estados sin programar la lógica de arrays a mano. |
| `<FileTree>` | `<Icon>` | Nativo o `react-folder-tree` | Un componente recursivo en React suele bastar. Librería solo si la complejidad lo justifica. |

---

## Stack definitivo

| Capa | Librería |
|------|----------|
| Estilos | Tailwind CSS (`@tailwindcss/vite` v4) |
| Iconos | `lucide-react` (control via props) — o Material Symbols si ya está en index.html |
| Data fetching | `@tanstack/react-query` |
| Layout / paneles | `react-resizable-panels` |
| Grafo | `@xyflow/react` |
| Editor | `@uiw/react-codemirror` |
| Drag & Drop | `@dnd-kit/core` |

---

## Por qué React Query como pegamento

En lugar de `useEffect` + `useState(loading)` por cada llamada:

```ts
// Antes (feo)
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
useEffect(() => { fetch(...).then(setData).finally(() => setLoading(false)) }, [jobId]);

// Con React Query
const { data: jobTimeline, isLoading } = useQuery({
  queryKey: ['timeline', source, jobId],
  queryFn: () => getJobTimeline(source, jobId),
});
```

Out of the box: caché, reintentos automáticos si el backend falla, background-refetch,
invalidación de caché en mutations, y devtools para inspeccionar el estado.
El mock client ya tiene las mismas firmas — cambiar `VITE_MOCK=true/false` es transparente.

---

## Packages a instalar

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
npm install react-resizable-panels
npm install @uiw/react-codemirror @codemirror/lang-markdown @codemirror/lang-json
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
npm install dagre @types/dagre
npm install lucide-react
# @xyflow/react ya está instalado
```
