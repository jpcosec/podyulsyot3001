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

> Fuente de verdad: `00_architecture.md`. Este árbol replica la estructura canónica.

```
src/
  components/                  # UI global (Diseño Atómico puro)
    atoms/
      Button.tsx
      Badge.tsx
      Tag.tsx
      Icon.tsx
      Spinner.tsx
      Kbd.tsx
    molecules/
      SplitPane.tsx            # wrapper de react-resizable-panels
      DiagnosticCard.tsx
      ControlPanel.tsx
    organisms/
      IntelligentEditor.tsx    ← migrar de sandbox/components/
      GraphCanvas.tsx
      FileTree.tsx
    layouts/
      AppShell.tsx             # LeftNav + <Outlet />
      JobWorkspaceShell.tsx    # Pipeline TopBar + <Outlet />
  features/                    # Lógica de negocio (Feature-Sliced)
    portfolio/
      api/usePortfolioSummary.ts
      components/PortfolioTable.tsx, DeadlineSidebar.tsx
    job-pipeline/
      api/useJobTimeline.ts, useViewOne.ts, useViewTwo.ts, useViewThree.ts, ...
      components/RequirementList.tsx, EvidenceBankPanel.tsx, MatchControlPanel.tsx, ...
    base-cv/
      api/useCvProfileGraph.ts
      components/CvGraphEditor.tsx
  pages/
    global/
      PortfolioDashboard.tsx   (A1)
      DataExplorer.tsx         (A2)
      BaseCvEditor.tsx         (A3)
    job/
      JobFlowInspector.tsx     (B0)
      ScrapeDiagnostics.tsx    (B1)
      ExtractUnderstand.tsx    (B2)
      Match.tsx                (B3)
      GenerateDocuments.tsx    (B4)
      PackageDeployment.tsx    (B5)
  types/
    api.types.ts               # PortfolioSummary, ViewOnePayload, GraphNode...
    ui.types.ts                # ReactFlow, DnD, editor state
  utils/
    cn.ts                      # clsx + tailwind-merge
  api/                         # client real (fetch wrapper)
  mock/                        # client mock + fixtures
  sandbox/
    components/IntelligentEditor.tsx   ← prototipo actual
    pages/IntelligentEditorPage.tsx
```

---

## Orden de construcción

> Fuente de verdad: `plan/index_checklist.md` (Fase 0–10).

```
Fase 0  → cn.ts, main.tsx, AppShell, JobWorkspaceShell, Badge, PortfolioDashboard, mock toggle, types/
Fase 1  → B0 JobFlowInspector
Fase 2  → A2 DataExplorer
Fase 3  → B1 ScrapeDiagnostics
Fase 4  → B2 ExtractUnderstand
Fase 5  → B3 Match
Fase 6  → B4 GenerateDocuments (PREP_MATCH)
Fase 7  → B5 PackageDeployment
Fase 8  → B4b Default Document Gates ⚠️ BLOCKED
Fase 9  → A3 BaseCvEditor
Fase 10 → B3b ApplicationContext ⚠️ BLOCKED
```
