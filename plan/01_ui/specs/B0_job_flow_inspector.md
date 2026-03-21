# Spec: Job Flow Inspector (Entrypoint del Job)

## 1. Objetivo del Operador
Al abrir un job, esta es la vista principal de contexto. El operador ve:
- En qué etapa está el pipeline y cuál es el estado de cada una
- Qué artefactos están disponibles en cada etapa (links directos)
- Si hay un bloqueo HITL activo, un CTA prominente para ir a resolverlo
- Metadatos del job (título, institución, deadline, score de match si existe)

Funciona como "hub de navegación" — desde aquí se navega a cualquier vista de etapa.

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/jobs/:source/:jobId/timeline` → `JobTimeline`
  ```ts
  {
    source, job_id, thread_id, current_node, status,
    stages: StageItem[],   // { stage, status, artifact_ref }
    artifacts: Record<string, string>,
    updated_at
  }
  ```

**Escritura:** Ninguna. Vista de solo lectura.

---

## 3. Composición de la UI y Layout

**Layout Base:** Columna central (sin right panel — el inspector es el main). Left nav persiste.

```
┌─ LeftNav ─┬───────────────────── Main (flex-1) ──────────────────────────┐
│           │  [Job header: título + institución + status badge]            │
│           │  [Pipeline timeline vertical — 8 etapas]                     │
│           │                                                               │
│           │  Cada etapa:                                                  │
│           │  [●]──[SCRAPE]────────[completed]──[artifact link]           │
│           │  [●]──[EXTRACT]───────[completed]──[artifact link]           │
│           │  [●]──[MATCH]─────────[completed]──[artifact link]           │
│           │  [◉]──[REVIEW_MATCH]──[paused_review]──[→ GO TO REVIEW]     │← CTA
│           │  [○]──[GENERATE]──────[pending]                              │
│           │  [○]──[RENDER]────────[pending]                              │
│           │  [○]──[PACKAGE]───────[pending]                              │
│           │                                                               │
│           │  [Run metadata panel: match score, deadline, last updated]   │
└───────────┴───────────────────────────────────────────────────────────────┘
```

**Componentes Core:**
- `<PipelineTimeline>` — lista vertical de etapas con conector vertical
- `<StageRow>` — fila de etapa: dot (colored) + nombre + status badge + artifact link
- `<JobMetaPanel>` — tarjeta con match score, deadline, thread_id, updated_at
- `<HitlCta>` — banner prominente cuando `status === "paused_review"` con botón que navega a la vista de review

**Stage dot colors:**
```
completed     → ● bg-primary (cyan filled)
paused_review → ● bg-secondary animate-pulse (amber pulsing)
running       → ● bg-secondary (amber static)
failed        → ● bg-error (salmon)
pending       → ○ border border-outline (grey empty)
```

**Componentes a Reciclar/Limpiar:**
- `JobStagePage.tsx` — extraer la lógica de timeline en `<PipelineTimeline>`, separar del tab system
- `StageStatusBadge.tsx` — adaptar colores al theme

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Fondo: `bg-surface`
- Pipeline container: `bg-surface-container-low panel-border tactical-glow` — ancho máximo centrado
- Conector vertical entre dots: `border-l-2 border-outline-variant/30 ml-[5px]`
- CTA banner HITL: `bg-secondary/10 border border-secondary/40 alert-glow`

**Tipografía:**
- Nombre job: `font-headline font-bold text-lg text-on-surface uppercase`
- Nombre de etapa: `font-headline uppercase tracking-widest text-sm`
- Status badge: `font-mono text-[10px] uppercase`
- Artifact link: `font-mono text-[10px] text-primary hover:underline`

**Interacciones Clave:**
- Click en nombre de etapa → navega a la vista de esa etapa (si tiene vista propia)
- Click en artifact link → navega a Data Explorer en ese path
- CTA "GO TO REVIEW" → navega a la vista de review correspondiente
- Pipeline nav del TopBar muestra etapa activa del job

**Estado Vacío / Error:**
- Job no encontrado: `NOT_FOUND` en mono + link de vuelta al portfolio
- Pipeline vacío (solo scrape pendiente): primera etapa con pulsing running dot
