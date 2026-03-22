# Spec B2 — Extract & Understand (HITL A)

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/ExtractUnderstand.tsx`
**Librerías:** `react-resizable-panels` · `@uiw/react-codemirror` · `@tanstack/react-query` · `lucide-react`
**Fase:** 4

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/views/ViewTwoDocToGraph.tsx` en branch `dev`  
**Legacy reference:** extraer shape del JSON de `view_extract_*.json` fixtures  
**To migrate:** mover lógica a `features/job-pipeline/` + aplicar CodeMirror + conectar via `useExtractState`

El LLM extrajo los requerimientos del job posting. El operador debe:
- Leer el texto fuente y ver qué fragmentos corresponden a cada requerimiento
- Verificar que cada requerimiento extraído es correcto (texto, prioridad)
- Editar texto o prioridad de requerimientos incorrectos
- Agregar requerimientos omitidos por el LLM
- Eliminar requerimientos duplicados o alucinados
- Aprobar la extracción para continuar al match

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v2/query/jobs/:source/:job_id/views/extract` → `ViewPayload<'extract'>`
  ```ts
  {
    view: 'extract', source, job_id,
    data: {
      source_markdown: string,
      requirements: RequirementItem[]   // { id, text, priority, spans, text_span }
    }
  }
  ```

**Escritura:**
- `PUT /api/v2/commands/jobs/:source/:job_id/state/extract_understand` — guarda borrador
- `POST /api/v2/commands/jobs/:source/:job_id/gates/review_match/decide` — no aplica a esta vista (extract no tiene gate propio actualmente)

---

## 3. Composición de la UI y Layout

**Layout:** `<SplitPane>` 50/50 + right control panel (w-80).

```
┌── Source Text (50%) ─────────┬── Requirements (50%) ──────┬── Control Panel ──┐
│ [SOURCE_TEXT header]          │ [EXTRACTED_REQS header]    │ [PHASE: EXTRACT]  │
│                               │                            │                   │
│ Texto markdown con             │ Lista RequirementItem:     │ [Technical tab]   │
│ spans resaltados al           │ [ID] [priority badge]      │ Selected req JSON │
│ hover de un req               │ texto editable             │                   │
│                               │ [spans count]              │ [Stage Actions]   │
│                               │                            │ [Commit]          │
│                               │ [+ Add Requirement]        │ [Discard]         │
└───────────────────────────────┴────────────────────────────┴───────────────────┘
```

**Interacción de spans:**
- Hover sobre `RequirementItem` → resalta spans en texto fuente: `bg-primary/20 border-x border-primary`
- Click en span resaltado → selecciona el requirement correspondiente

**Componentes Core:**
- `<SourceTextPane>` — CodeMirror read-only con decoraciones de span highlight
- `<RequirementList>` — lista de `<RequirementItem>` editables (organismo)
- `<RequirementItem>` — card con ID badge + priority selector + texto editable inline
- `<ExtractControlPanel>` — right panel amber, tabs Technical / Stage Actions

**Priority badge:**
```
must → bg-secondary/10 text-secondary border border-secondary/30  [MUST]
nice → bg-outline/10 text-on-muted border border-outline/30       [NICE]
```

---

## 4. Estilos (Terran Command)

- Panel source: `bg-surface-low border-r border-outline/20`
- Panel reqs: `bg-surface`
- Control panel: `bg-background border-l border-secondary/20`
- Control panel header: `text-secondary font-headline uppercase tracking-widest`
- Span highlight: `bg-primary/15 border-x border-primary/60 px-0.5`
- Span hover activo: `bg-primary/30 border-primary`
- ID req: `font-mono text-[9px] text-primary/60`
- Texto req: `font-body text-sm text-on-surface`

**Interacciones:**
- `Ctrl+S` → guarda estado (useMutation)
- `Ctrl+Enter` → commit y navega al match
- `Delete` en req seleccionado → eliminar (confirm si `priority === "must"`)
- `Escape` → deseleccionar req, quitar highlights
- `+` button → agrega nuevo req al final de la lista

**Estado Vacío:** `NO_REQUIREMENTS_EXTRACTED` + botón add manual
**Estado Error:** banner `EXTRACTION_FAILED` con opción re-run o entrada manual

---

## 5. Archivos a crear

```
src/features/job-pipeline/
  api/
    useExtractState.ts            useQuery + useMutation → PUT /commands/.../state/extract_understand
  components/
    SourceTextPane.tsx            CodeMirror read-only + span decorations
    RequirementList.tsx           organismo: lista de items editables
    RequirementItem.tsx           card individual editable
    ExtractControlPanel.tsx       right panel amber con acciones HITL
src/pages/job/
  ExtractUnderstand.tsx           TONTO: useParams + hooks + render
```

---

## 6. Definition of Done

```
[ ] ExtractUnderstand renderiza con SplitPane 50/50 para job 201397 (mock)
[ ] SourceTextPane muestra el markdown del mock (texto TU Berlin real)
[ ] RequirementList muestra los 14 requerimientos del mock
[ ] Hover en un RequirementItem resalta los spans correspondientes en el texto
[ ] Editar el texto de un req actualiza el estado local
[ ] Ctrl+S ejecuta useMutation sin error (mock no-op)
[ ] Ctrl+Enter navega a /match después de guardar
[ ] Botón + agrega un RequirementItem vacío al final de la lista
[ ] Delete en req "must" muestra confirm dialog
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/201397/extract`

1. Verificar que el SplitPane renderiza con texto fuente a la izquierda y lista de reqs a la derecha
2. Hover sobre el primer `<RequirementItem>` → verificar que aparece highlight en el SourceTextPane
3. Click en un req → verificar que el `<ExtractControlPanel>` muestra el JSON del req seleccionado
4. Editar el texto de un req + presionar `Ctrl+S` → verificar que no hay errores en consola
5. Presionar `Ctrl+Enter` → verificar navegación a `/jobs/tu_berlin/201397/match`

---

## 8. Git Workflow

### Commit al cerrar la fase

```
feat(ui): implement extract & understand (B2)

- SourceTextPane with CodeMirror and span highlight decorations
- RequirementList with editable RequirementItems
- ExtractControlPanel with JSON readout and stage actions
- Span hover interaction for requirement selection
- Connected to useExtractState hook
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented B2 Extract & Understand: source text pane with span highlighting,
  editable requirement list, and extract control panel.
```

### Checklist update (index_checklist.md)

- [x] B2 Extract & Understand
