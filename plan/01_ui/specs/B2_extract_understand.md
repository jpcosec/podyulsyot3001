# Spec: Extract & Understand (HITL A)

## 1. Objetivo del Operador
El LLM extrajo los requerimientos del job posting. El operador debe:
- Leer el texto fuente original y ver qué fragmentos fueron usados para cada requerimiento
- Verificar que cada requerimiento extraído es correcto (texto, prioridad)
- Editar texto o prioridad de requerimientos incorrectos
- Agregar requerimientos que el LLM omitió
- Eliminar requerimientos duplicados o alucinados
- Aprobar la extracción para continuar al match

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/jobs/:source/:jobId/view2` → `ViewTwoPayload`
  ```ts
  {
    source, job_id,
    source_markdown: string,           // texto fuente completo
    requirements: RequirementItem[]    // { id, text, priority, spans, text_span }
  }
  ```

**Escritura:**
- `PUT /api/v1/jobs/:source/:jobId/editor/extract_understand/state` → guarda estado editado

---

## 3. Composición de la UI y Layout

**Layout Base:** SplitScreen 50/50 — izquierda texto fuente, derecha lista de requerimientos. Right panel (control panel w-80) con acciones HITL.

```
┌─ LeftNav ─┬──── Source Text (50%) ────┬──── Requirements (50%) ────┬── Control Panel ──┐
│           │ [header: SOURCE_TEXT]     │ [header: EXTRACTED_REQS]  │ [PHASE: EXTRACT]  │
│           │                          │                            │                   │
│           │ Texto markdown con        │ Lista de RequirementItem   │ [Technical tab]   │
│           │ spans resaltados al       │ Cada item:                 │ Selected req JSON │
│           │ hover de un req           │ [ID] [priority badge]      │                   │
│           │                          │ texto editable (Slate)     │ [Stage Actions]   │
│           │                          │ [spans count]              │ + Commit          │
│           │                          │                            │ × Discard         │
│           │                          │ [+ Add Requirement]        │                   │
└───────────┴──────────────────────────┴────────────────────────────┴───────────────────┘
```

**Interacción de spans:**
- Hover sobre un `RequirementItem` → resalta los spans correspondientes en el texto fuente con `bg-primary/20 border-x border-primary`
- Click en span resaltado en texto → selecciona el requirement

**Componentes Core:**
- `<SourceTextPane>` — markdown viewer con sistema de highlight por span
- `<RequirementList>` — lista de `<RequirementItem>` editables
- `<RequirementItem>` — card con ID badge + priority selector + texto editable inline
- `<ControlPanel>` — right sidebar amber con tabs Technical / Stage Actions
- `<AddRequirementForm>` — inline form al bottom de la lista

**Componentes a Reciclar/Limpiar:**
- `ViewTwoDocToGraph.tsx` — es el antecedente directo de esta vista. Extraer el Slate editor,
  rediseñar layout con el nuevo theme.

**Priority badge:**
```
must → bg-secondary/10 text-secondary border border-secondary/30  [MUST]
nice → bg-outline/10 text-outline border border-outline/30         [NICE]
```

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Panel izquierdo (source): `bg-surface-container-low border-r border-outline-variant/20`
- Panel derecho (reqs): `bg-surface`
- Control panel: `bg-[#0c0e10] border-l border-secondary/20`
- Control panel header: `text-secondary font-headline uppercase tracking-widest`
- Span highlight en texto: `bg-primary/15 border-x border-primary/60 px-0.5`
- Span hover activo: `bg-primary/30 border-primary`

**Tipografía:**
- Header panels: `font-mono text-[10px] text-outline uppercase tracking-[0.2em]`
- ID de requerimiento: `font-mono text-[9px] text-primary/60`
- Texto de requerimiento: `font-body text-sm text-on-surface`
- Execution logs en control panel: `font-mono text-[10px] border-l border-primary/20 pl-3`

**Interacciones Clave:**
- `Ctrl+S` → guarda estado actual
- `Ctrl+Enter` → commit y avanzar al match
- `Delete` en req seleccionado → eliminar (con confirm si `priority === "must"`)
- `Escape` → deseleccionar req activo, quitar highlights
- `+` button → agrega nuevo req al final de la lista

**Estado Vacío:**
- Sin requerimientos: mensaje `NO_REQUIREMENTS_EXTRACTED` + botón de add manual
- Source text vacío: `SOURCE_TEXT_UNAVAILABLE`

**Estado Error:**
- LLM falló en extracción: banner `EXTRACTION_FAILED` con opción de re-run o entrada manual
- JSON schema inválido al guardar: highlight del campo inválido en rojo

---

## Notas de Implementación

- El Slate editor por requerimiento es `singleLine` (solo texto, sin formato)
- Los `spans` son opcionales — si `text_span === null`, no se hace highlight
- La aprobación final escribe al `editor/extract_understand/state` endpoint y navega automáticamente al Match
