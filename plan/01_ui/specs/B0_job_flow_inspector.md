# Spec B0 — Job Flow Inspector

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/JobFlowInspector.tsx`
**Librerías:** `@tanstack/react-query` · `lucide-react`
**Fase:** 2

---

## 1. Objetivo del Operador

Hub de navegación del job. El operador ve:
- En qué etapa está el pipeline y el estado de cada una
- Qué artefactos están disponibles (links directos)
- Si hay un bloqueo HITL activo, un CTA prominente para ir a resolverlo
- Metadatos del job (título, institución, deadline, score de match si existe)

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

**Escritura:** Ninguna.

---

## 3. Composición de la UI y Layout

**Layout:** Columna central, sin panel lateral. El inspector ocupa el main completo.

```
┌─────────────── Main (flex-1, max-w-2xl mx-auto) ───────────────┐
│  [Job header: título + institución + status badge]              │
│                                                                  │
│  [HitlCtaBanner — solo si paused_review]                        │
│                                                                  │
│  [PipelineTimeline vertical]                                     │
│  ● SCRAPE ────── completed ── [artifact link]                   │
│  ● EXTRACT ───── completed ── [artifact link]                   │
│  ● MATCH ──────── completed ── [artifact link]                  │
│  ◉ REVIEW_MATCH ─ paused_review ── [→ GO TO REVIEW]           │← CTA
│  ○ GENERATE ───── pending                                       │
│  ○ RENDER ──────── pending                                      │
│  ○ PACKAGE ──────── pending                                     │
│                                                                  │
│  [JobMetaPanel: match score, deadline, thread_id, updated_at]  │
└──────────────────────────────────────────────────────────────────┘
```

**Componentes Core:**
- `<PipelineTimeline>` — lista vertical de etapas con conector
- `<StageRow>` — dot (colored) + nombre + Badge status + artifact link
- `<JobMetaPanel>` — tarjeta con score, deadline, thread_id, updated_at
- `<HitlCtaBanner>` — banner amber prominente cuando `status === "paused_review"`

**Stage dot colors:**
```
completed     → text-primary (●)
paused_review → text-secondary animate-pulse (◉)
running       → text-secondary (●)
failed        → text-error (●)
pending       → text-on-muted border border-outline (○)
```

---

## 4. Estilos (Terran Command)

- Fondo: `bg-surface`
- Pipeline container: `bg-surface-container-low panel-border tactical-glow`
- Conector vertical: `border-l-2 border-outline/20 ml-[5px]`
- CTA banner HITL: `bg-secondary/10 border border-secondary/40 alert-glow`
- Nombre job: `font-headline font-bold text-lg text-on-surface uppercase`
- Nombre etapa: `font-headline uppercase tracking-widest text-sm`
- Artifact link: `font-mono text-[10px] text-primary hover:underline`

**Interacciones:**
- Click en nombre de etapa → navega a la vista de esa etapa
- Click en artifact link → navega a Data Explorer en ese path
- CTA "GO TO REVIEW" → navega a la vista de review correspondiente

**Estado Error:** `NOT_FOUND` + link al portfolio
**Estado Vacío:** primera etapa con dot pulsando (running)

---

## 5. Archivos a crear

```
src/features/job-pipeline/
  api/
    useJobTimeline.ts             useQuery(['timeline', source, jobId])
  components/
    PipelineTimeline.tsx          lista vertical de etapas
    StageRow.tsx                  fila individual de etapa
    HitlCtaBanner.tsx             banner amber de acción HITL
    JobMetaPanel.tsx              tarjeta de metadata del job
src/pages/job/
  JobFlowInspector.tsx            TONTO: useParams + hook + render
```

---

## 6. Definition of Done

```
[ ] JobFlowInspector renderiza sin errores para job 201397 (mock)
[ ] PipelineTimeline muestra todas las etapas con dots del color correcto
[ ] HitlCtaBanner visible cuando status=paused_review
[ ] Click en etapa completada navega a la ruta correspondiente
[ ] JobMetaPanel muestra thread_id y updated_at del mock
[ ] Estado loading muestra Spinner
[ ] Estado error muestra NOT_FOUND con link al portfolio
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/201397`

1. Verificar que `<PipelineTimeline>` renderiza con las etapas del job
2. Verificar que el dot de `review_match` tiene clase `animate-pulse` (paused_review)
3. Verificar que `<HitlCtaBanner>` está visible con botón "GO TO REVIEW"
4. Click en "GO TO REVIEW" → verificar navegación a `/jobs/tu_berlin/201397/match`
5. Navegar a `/jobs/tu_berlin/999001` → verificar que HitlCtaBanner NO aparece (status=completed)
