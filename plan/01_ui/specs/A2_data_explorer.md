# Spec A2 — Data Explorer

**Feature:** `src/features/explorer/`
**Page:** `src/pages/global/DataExplorer.tsx`
**Librerías:** `react-resizable-panels` · `@uiw/react-codemirror` · `lucide-react`
**Fase:** 2

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/views/ViewTwoDocToGraph.tsx` en branch `dev`  
**Legacy reference:** extraer shape del JSON de `view_extract_*.json` fixtures  
**To migrate:** extraer lógica de browse a `features/explorer/` + aplicar estética Terran Command + conectar via `useExplorerBrowse`

Navegar el filesystem de `data/jobs/` para inspeccionar artefactos crudos — JSONs aprobados, propuestos, trazas de error, screenshots. No es una vista de edición; es diagnóstico y auditoría.

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/explorer/browse?path=<path>` → `ExplorerPayload`
  ```ts
  {
    path: string,
    is_dir: boolean,
    entries?: ExplorerEntry[],
    content_type?: "text" | "image" | "binary" | "too_large",
    content?: string | null
  }
  ```

**Escritura:** Ninguna.

---

## 3. Composición de la UI y Layout

**Layout:** `<SplitPane>` 30/70 — árbol izquierdo + preview derecho.

```
┌── col-left (30%) ─────┬── col-right (70%) ───────────────────┐
│ Path breadcrumb        │ [header: ruta actual + tipo]         │
│                        │                                      │
│ ► tu_berlin/           │  Si directorio:                      │
│   ► 201397/            │    grid de carpetas/archivos         │
│     ► nodes/           │    con iconos por tipo               │
│       ► match/         │                                      │
│         approved/ ←   │  Si archivo JSON/text:               │
│                        │    CodeMirror read-only              │
│                        │    syntax highlighting               │
│                        │                                      │
│                        │  Si imagen:                          │
│                        │    img centrada + metadata           │
└────────────────────────┴──────────────────────────────────────┘
```

**Componentes Core:**
- `<ExplorerTree>` — árbol colapsable, íconos por tipo (Lucide)
- `<BreadcrumbNav>` — path segmentado, cada segmento clickeable
- `<FilePreview>` — dispatcher: `<JsonPreview>` / `<MarkdownPreview>` / `<ImagePreview>` / `<BinaryStub>`
- `<JsonPreview>` — CodeMirror en modo `json`, read-only, tema oscuro

**Íconos por extensión (lucide-react):**
```
.json    → FileJson  (cyan)
.md      → FileText  (cyan dim)
.png/.jpg→ Image     (outline)
.pdf     → FileType  (error/salmon)
carpeta  → Folder    (cyan dim)
```

---

## 4. Estilos (Terran Command)

- Panel árbol: `bg-surface-container-low border-r border-outline/20`
- Ítem activo árbol: `bg-primary/10 text-primary border-r-2 border-primary`
- Panel preview: `bg-surface`
- Header preview: `bg-surface-high px-4 py-2 font-mono text-[10px] text-on-muted uppercase`
- CodeMirror: tema `tokyoNightStorm` o tema custom con `bg-surface`

**Interacciones:**
- Click carpeta → expande árbol + navega en panel derecho
- Click archivo → carga preview (nueva query)
- Breadcrumb click → sube niveles

**Estado Vacío:** `DIRECTORY_EMPTY`, `BINARY_CONTENT: NO_PREVIEW`, `FILE_EXCEEDS_LIMIT`
**Estado Error:** path no encontrado → icono `AlertTriangle` + path en rojo

---

## 5. Archivos a crear

```
src/features/explorer/
  api/
    useExplorerBrowse.ts          useQuery(['explorer', path])
  components/
    ExplorerTree.tsx              árbol recursivo colapsable
    BreadcrumbNav.tsx             segmentos clickeables
    FilePreview.tsx               dispatcher por tipo
    JsonPreview.tsx               CodeMirror read-only json
    MarkdownPreview.tsx           CodeMirror read-only markdown
    ImagePreview.tsx              img + metadata
src/pages/global/
  DataExplorer.tsx                TONTO: estado de path en URL search params
```

---

## 6. Definition of Done

```
[ ] DataExplorer renderiza con SplitPane 30/70 redimensionable
[ ] ExplorerTree muestra las 2 carpetas del mock (root fixture)
[ ] Click en carpeta expande el árbol y actualiza el panel derecho
[ ] Click en archivo JSON carga CodeMirror read-only con syntax highlighting
[ ] BreadcrumbNav actualiza al navegar
[ ] Estado loading visible mientras fetchea (Spinner en panel derecho)
[ ] Estado vacío muestra DIRECTORY_EMPTY
[ ] Archivo de imagen muestra <img> centrada
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/explorer`

1. Verificar que el SplitPane renderiza con dos paneles
2. Expandir la carpeta `tu_berlin/` en el árbol → verificar que aparece `201397/`
3. Navegar hasta `nodes/match/approved/` → hacer click en `state.json` → verificar que CodeMirror carga JSON con colores
4. Click en breadcrumb `match` → verificar que el panel derecho vuelve al directorio

---

## 8. Git Workflow

### Commit al cerrar la fase

```
feat(ui): implement data explorer (A2)

- ExplorerTree recursive collapsible file browser
- BreadcrumbNav with clickable path segments
- FilePreview dispatcher for JSON/MD/image/binary
- JsonPreview with CodeMirror syntax highlighting
- Connected to useExplorerBrowse hook
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented A2 Data Explorer: recursive file tree with JSON/MD/image preview
  and CodeMirror syntax highlighting.
```

### Checklist update (index_checklist.md)

- [x] A2 Data Explorer
