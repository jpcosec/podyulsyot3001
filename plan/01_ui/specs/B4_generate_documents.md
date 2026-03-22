# Spec B4 — Generate Documents (HITL C — Sculpting) — PREP_MATCH

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/GenerateDocuments.tsx`
**Librerías:** `react-resizable-panels` · `@uiw/react-codemirror` · `@tanstack/react-query` · `lucide-react`
**Fase:** 6

> **Nota PREP_MATCH vs DEFAULT:** Este spec describe la vista de PREP_MATCH donde los 3 documentos
> se generan y revisan juntos en un solo gate (3 tabs simultáneos). En el **DEFAULT pipeline**,
> cada documento tiene su propio gate HITL separado — ver **spec B4b**. La UI base es la misma:
> solo cambia qué tabs están activos/locked a la vez.

---

## 1. Objetivo del Operador

El LLM generó los tres documentos de aplicación. El operador debe:
- Leer el CV adaptado, la cover letter y el email propuestos
- Editar libremente el texto (tono, estructura, longitud)
- Ver qué fragmentos del documento mapean a qué evidencias del perfil
- Aprobar cada documento por separado o todos juntos
- Pedir regeneración con feedback si el output es insatisfactorio

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v2/query/jobs/:source/:job_id/views/documents` → `ViewPayload<'documents'>`
  ```ts
  {
    view: 'documents', source, job_id,
    data: {
      documents: { cv: string, motivation_letter: string, application_email: string },
      nodes: GraphNode[],
      edges: GraphEdge[]
    }
  }
  ```

**Escritura:**
- `PUT /api/v2/commands/jobs/:source/:job_id/documents/:doc_key` → `{ markdown: string }` — edita contenido
- `POST /api/v2/commands/jobs/:source/:job_id/gates/review_match/decide` — APPROVE_ALL (PREP_MATCH)

---

## 3. Composición de la UI y Layout

**Layout:** `<SplitPane>` 70/30 — editor principal + context panel.

```
┌── Tab Bar + Editor (70%) ───────────────────────┬── Context Panel (30%) ──┐
│ [CV] [COVER_LETTER] [EMAIL]    [SAVE] [APPROVE]  │ [PHASE: SCULPTING]     │
│──────────────────────────────────────────────── │                         │
│                                                  │ Mini match graph        │
│  CodeMirror (markdown mode, editable)            │ (read-only, estático)   │
│  [contenido del documento activo]               │                         │
│                                                  │ Evidence usada:         │
│                                                  │ [EV-005] EEG Research  │
│                                                  │ [EV-006] ITS Project   │
│                                                  │                         │
│                                                  │ [REQUEST REGEN]         │
│                                                  │ [APPROVE ALL]           │
└──────────────────────────────────────────────────┴─────────────────────────┘
```

**Tab indicator de estado:**
```
Aprobado:          [✓ CV]  → text-primary border-b-2 border-primary
Editado sin guardar: [● CV] → text-secondary (amber dot)
Sin editar:          [CV]   → text-on-muted
```

**Componentes Core:**
- `<DocumentTabs>` — tab bar con 3 docs + indicadores de estado
- `<DocumentEditor>` — CodeMirror editable en modo markdown
- `<ContextPanel>` — right panel con mini-grafo + lista de evidencias
- `<DocApproveBar>` — sticky bottom: Save (Ctrl+S) + Approve (Ctrl+Enter)
- `<RegenModal>` — modal con textarea feedback + botón re-run

---

## 4. Estilos (Terran Command)

- Tab bar: `bg-surface-container border-b border-outline/20`
- Editor: `bg-surface-low font-body text-sm`
- Context panel: `bg-background border-l border-secondary/20`
- Context panel header: `text-secondary font-headline uppercase`
- Evidence IDs: `font-mono text-[9px] text-primary/60`
- Botones acción: `font-headline font-bold uppercase tracking-widest text-xs`

**Interacciones:**
- `Ctrl+S` → guarda documento activo (useMutation)
- `Ctrl+Enter` → aprueba documento activo (marca tab con ✓)
- Tab click → cambia documento (warning si hay cambios sin guardar)
- "APPROVE ALL" → aprueba los 3 docs + navega al deployment

**Estado Vacío:** `NO_CONTENT_GENERATED — REQUEST_REGEN`
**Estado Error:** toast amber `SAVE_FAILED` / banner rojo `GENERATION_FAILED`

---

## 5. Archivos a crear

```
src/features/job-pipeline/
  api/
    useViewDocuments.ts           useQuery(['view', 'documents', source, jobId])
    useDocumentSave.ts            useMutation → PUT /commands/.../documents/:doc_key
    useGateDecide.ts              useMutation → POST /commands/.../gates/.../decide
  components/
    DocumentTabs.tsx              tab bar con estados de aprobación
    DocumentEditor.tsx            CodeMirror markdown editable
    ContextPanel.tsx              mini-grafo + lista de evidencias
    DocApproveBar.tsx             sticky bottom save/approve
    RegenModal.tsx                modal feedback + re-run
src/pages/job/
  GenerateDocuments.tsx           TONTO: useParams + hooks + render
```

---

## 6. Definition of Done

```
[ ] GenerateDocuments renderiza con 3 tabs para job 999001 (mock)
[ ] Tab CV activo por defecto con contenido del mock en DocumentEditor
[ ] Cambiar tab carga el contenido del documento correspondiente
[ ] Editar texto en DocumentEditor actualiza estado local
[ ] Ctrl+S ejecuta useMutation sin error
[ ] Tab muestra ● (amber) cuando hay cambios sin guardar
[ ] Ctrl+Enter marca el tab con ✓ (aprobado)
[ ] "REQUEST REGEN" abre RegenModal
[ ] "APPROVE ALL" navega a /jobs/tu_berlin/999001/sculpt (o deployment)
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/999001/sculpt`

1. Verificar que los 3 tabs (CV / COVER_LETTER / EMAIL) son visibles
2. Verificar que el tab CV está activo y el editor tiene contenido
3. Click en tab COVER_LETTER → verificar que el editor carga el contenido de la carta
4. Editar texto en el editor → verificar que el tab muestra el dot amber (●)
5. Presionar `Ctrl+S` → verificar que el dot desaparece (guardado)
6. Presionar `Ctrl+Enter` → verificar que el tab muestra ✓
7. Click en "REQUEST REGEN" → verificar que `<RegenModal>` aparece con textarea
