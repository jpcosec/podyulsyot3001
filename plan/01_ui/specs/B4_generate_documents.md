# Spec: Generate Documents (HITL C — Sculpting)

## 1. Objetivo del Operador
El LLM generó los tres documentos de aplicación. El operador debe:
- Leer el CV adaptado, la cover letter y el email propuestos por el LLM
- Editar libremente el texto (esculpir tono, reordenar, completar huecos)
- Ver qué fragmentos del documento mapean a qué evidencias del perfil (panel de contexto)
- Aprobar cada documento por separado o todos juntos
- Pedir regeneración con feedback si el output es insatisfactorio

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/jobs/:source/:jobId/view3` → `ViewThreePayload`
  ```ts
  {
    source, job_id,
    documents: {
      cv: string,
      motivation_letter: string,
      application_email: string
    },
    nodes: GraphNode[],    // para el mini-grafo de contexto
    edges: GraphEdge[]
  }
  ```
- `GET /api/v1/jobs/:source/:jobId/documents/:docKey` → doc individual con `artifact_ref`

**Escritura:**
- `PUT /api/v1/jobs/:source/:jobId/documents/:docKey` → `{ content: string }`

---

## 3. Composición de la UI y Layout

**Layout Base:** Tabs horizontales (CV / Cover Letter / Email) + editor de texto principal + right panel de contexto.

```
┌─ LeftNav ─┬──── Tab Bar ─────────────────────────────────────────┬── Context Panel (w-72) ──┐
│           │ [CV] [COVER_LETTER] [EMAIL]           [SAVE] [APPROVE]│ [PHASE: SCULPTING]       │
│           ├──────────────────────────────────────────────────────│                          │
│           │                                                       │ Mini match graph         │
│           │  Rich Text Editor (Slate)                            │ (stripped down, static)  │
│           │                                                       │                          │
│           │  [contenido del documento activo]                    │ Evidence usada:          │
│           │                                                       │ [EV-005] EEG Research   │
│           │  Selección de texto → tooltip con "link to evidence" │ [EV-006] ITS Project    │
│           │                                                       │                          │
│           │                                                       │ [REQUEST REGEN]          │
│           │                                                       │ [APPROVE ALL & PROCEED]  │
└───────────┴───────────────────────────────────────────────────────┴──────────────────────────┘
```

**Componentes Core:**
- `<DocumentTabs>` — tab bar con los 3 documentos + indicadores de aprobación
- `<DocumentEditor>` — Slate rich text editor (sin markdown, texto plano estructurado)
- `<ContextPanel>` — right sidebar con mini-grafo de match + lista de evidencias usadas
- `<DocApproveBar>` — sticky bottom bar con Save (Ctrl+S) + Approve doc (Ctrl+Enter)
- `<RegenModal>` — modal con textarea de feedback + botón de re-run

**Tab indicator de estado:**
```
Aprobado: [✓ CV]           → text-primary border-b-2 border-primary
Editado sin guardar: [● CV] → text-secondary (amber dot)
Sin editar: [CV]            → text-outline
```

**Componentes a Reciclar/Limpiar:**
- `ViewThreeGraphToDoc.tsx` — base a rediseñar. Mantener lógica de Slate, rediseñar layout y estilos.
- El mini-grafo puede reutilizar `<GraphCanvas>` en modo read-only, tamaño reducido.

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Tab bar: `bg-surface-container border-b border-outline-variant/20`
- Editor principal: `bg-surface-container-low` — texto `font-body text-sm text-on-surface leading-relaxed`
- Context panel: `bg-[#0c0e10] border-l border-secondary/20`
- Context panel header: `text-secondary font-headline uppercase`
- Save bar bottom: `bg-surface-container-high border-t border-outline-variant/20`

**Tipografía:**
- Tab labels: `font-headline uppercase tracking-widest text-xs`
- Editor: `font-body text-sm` — mantiene tipografía legible para documentos largos
- Evidence IDs en context: `font-mono text-[9px] text-primary/60`
- Botones de acción: `font-headline font-bold uppercase tracking-widest text-xs`

**Interacciones Clave:**
- `Ctrl+S` → guarda documento activo (`saveDocument`)
- `Ctrl+Enter` → aprueba documento activo (marca tab con ✓)
- Tab click → cambia documento (con warning si hay cambios sin guardar)
- Selección de texto en editor → muestra tooltip "LINK_TO_EVIDENCE" (futura funcionalidad)
- `Ctrl+Z` / `Ctrl+Y` → undo/redo del editor Slate

**Estado Vacío:**
- Documento sin contenido: `NO_CONTENT_GENERATED — REQUEST_REGEN`

**Estado Error:**
- Fallo en save: toast `SAVE_FAILED` en amber
- LLM generation failed: banner rojo `GENERATION_FAILED` con opción de re-run
- Schema mismatch en docKey: `UNKNOWN_DOCUMENT_KEY: [key]`

---

## Notas de Implementación

- Los 3 documentos se cargan al abrir la vista — tabs cambian entre los ya cargados (no re-fetch)
- `approved` se trackea en estado local del componente — solo persiste al backend si se hace "Approve All & Proceed"
- El mini-grafo en el context panel es estático (no interactivo) — solo muestra las conexiones para recordarle al operador qué evidencias usó el LLM
- La futura funcionalidad de "link texto ↔ evidencia" (anotación) va en HITL C v2, no en este sprint
