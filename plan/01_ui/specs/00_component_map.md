# Component Map — Terran Command UI

Mapa de componentes para el rediseño. Define qué vistas existen, cómo se componen,
y qué átomos consume cada molécula.

---

## Vistas y Layout

| Spec | Vista | Layout Base | Main | Secundarios |
|------|-------|-------------|------|-------------|
| A1 | Portfolio Dashboard | Grid 9/3 | `<PortfolioTable>` `<ProgressSegmented>` | `<DeadlineSensors>` `<SystemStats>` |
| A2 | Data Explorer | `<SplitPane>` 30/70 | `<IntelligentEditor mode="fold">` | `<FileTree>` |
| A3 | Base CV Editor | Grid 70/30 | `<GraphCanvas>` (nodos CV/Skills) | `<NodeInspectorSidebar>` |
| B0 | Job Flow Inspector | Columna única | `<PipelineTimeline>` `<HitlCtaBanner>` | — |
| B1 | Scrape Diagnostics | Columna + Control | `<DiagnosticCard>` `<ImagePreview>` | `<ScrapeControlPanel>` |
| B2 | Extract & Understand | `<SplitPane>` 50/50 | `<IntelligentEditor mode="tag-hover">` `<RequirementList>` | `<ExtractControlPanel>` |
| B3 | Match | `<SplitPane>` 3 col | `<GraphCanvas>` (edges evaluados) | `<EvidenceBankSidebar>` `<MatchControlPanel>` |
| B4 | Generate Documents | `<SplitPane>` 50/50 | `<IntelligentEditor mode="diff">` `<DocumentTabs>` | `<PackageControlPanel>` |

---

## Moléculas → Átomos

| Molécula | Átomos que consume | Rol de cada átomo |
|----------|--------------------|-------------------|
| `<IntelligentEditor>` | `<Tag>` `<Badge>` `<Icon>` | `<Tag>` resalta spans en el texto. `<Badge>` aparece en el hover card. |
| `<GraphCanvas>` | `<Badge>` `<Icon>` | `<Badge>` muestra scores en los edges. `<Icon>` en los nodos. |
| `<PortfolioTable>` | `<Badge>` `<Icon>` | `<Badge status="verified\|pending">` para estado del job. |
| `<HitlCtaBanner>` | `<Button>` `<Icon>` | Botón gigante `variant="primary"` para ir al review. |
| `<RequirementList>` | `<Badge>` `<Button>` `<Icon>` | `<Badge>` para prioridad (must/nice). `<Button variant="ghost">` para borrar. |
| `<EvidenceBankSidebar>` | `<Badge>` `<Icon>` | `<Badge>` para categoría (skill/project). `<Icon name="drag_indicator">`. |
| `<FileTree>` | `<Icon>` | `<Icon>` dinámico según extensión (`.json`, `.md`, carpeta). |
| `<ControlPanel>` (todos) | `<Button>` `<Spinner>` `<Kbd>` | `<Button>` para commit/guardar. `<Spinner>` mientras guarda. `<Kbd>` para atajos. |

---

## Átomos base (a construir primero)

| Átomo | Props clave | Notas |
|-------|-------------|-------|
| `<Button>` | `variant: primary\|ghost\|danger` `size: sm\|md` `loading?: boolean` | `loading` muestra `<Spinner>` inline |
| `<Badge>` | `variant: primary\|secondary\|success\|muted` `size: xs\|sm` | Colores del design system. Border-radius 0. |
| `<Tag>` | `id` `category: skill\|req\|risk` `onHover` `onClick` | Inline span con `border-l-2` color-coded |
| `<Icon>` | `name: string` `size: xs\|sm\|md` | Lucide icons wrapeado con tamaño y color coherente |
| `<Spinner>` | `size: xs\|sm\|md` | Spinner CSS, color primario |
| `<Kbd>` | `keys: string[]` | Muestra atajos de teclado `Ctrl+S` con estilo mono |

---

## Modo de `<IntelligentEditor>`

El mismo componente se usa en tres vistas con comportamiento distinto:

| Modo | Vista | Comportamiento |
|------|-------|----------------|
| `fold` | A2 Data Explorer | Solo renderiza texto con syntax highlighting. Sin tags interactivos. |
| `tag-hover` | B2 Extract | Tags resaltan spans. Hover muestra card. Click pina al sidebar. |
| `diff` | B4 Generate Docs | Muestra diff entre versión anterior y generada. Tags de cambio (add/remove). |

---

## Árbol de archivos target

```
src/
  atoms/
    Button.tsx
    Badge.tsx
    Tag.tsx
    Icon.tsx
    Spinner.tsx
    Kbd.tsx
  molecules/
    IntelligentEditor.tsx    ← ya existe en sandbox/components/ (migrar aquí)
    GraphCanvas.tsx
    PortfolioTable.tsx
    HitlCtaBanner.tsx
    RequirementList.tsx
    EvidenceBankSidebar.tsx
    FileTree.tsx
    ControlPanel/
      ExtractControlPanel.tsx
      MatchControlPanel.tsx
      PackageControlPanel.tsx
      ScrapeControlPanel.tsx
  layout/
    AppShell.tsx             ← sidebar nav + main area
    SplitPane.tsx
  pages/
    PortfolioPage.tsx        (A1)
    DataExplorerPage.tsx     (A2)
    CvEditorPage.tsx         (A3)
    JobFlowPage.tsx          (B0)
    ScrapePage.tsx           (B1)
    ExtractPage.tsx          (B2)
    MatchPage.tsx            (B3)
    DocumentsPage.tsx        (B4)
  sandbox/
    components/
      IntelligentEditor.tsx  ← prototipo actual
    pages/
      IntelligentEditorPage.tsx
  api/         ← no tocar
  mock/        ← no tocar
  types/       ← no tocar
```

---

## Orden de construcción

```
1. Átomos        → Button, Badge, Tag, Icon, Spinner, Kbd
2. Layout        → AppShell (sidebar + main), SplitPane
3. Moléculas     → IntelligentEditor (migrar), GraphCanvas, PortfolioTable, HitlCtaBanner
4. Pages A       → A1 Portfolio, A2 Data Explorer, A3 CV Editor
5. Pages B       → B0 Job Flow, B2 Extract, B3 Match, B4 Documents
6. ControlPanels → uno por vista, se construyen con su page
```
