# Spec: Dashboard / Portfolio

## 1. Objetivo del Operador
El operador entra aquí como pantalla de inicio. Debe poder:
- Ver de un vistazo cuántos jobs están activos, en revisión, completados o fallidos
- Identificar cuál es el próximo job que requiere su atención (HITL bloqueado)
- Navegar a un job específico con un click
- Ver los deadlines más urgentes en el sidebar

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/portfolio/summary` → `PortfolioSummary`
  ```ts
  {
    totals: { jobs, completed, pending_review, running, failed },
    jobs: JobListItem[]  // { source, job_id, thread_id, current_node, status, updated_at }
  }
  ```

**Escritura:** Ninguna. Vista de solo lectura.

---

## 3. Composición de la UI y Layout

**Layout Base:** 12-col grid. `col-span-9` main + `col-span-3` sidebar derecho.

```
┌────────────────────── col-9 ──────────────────┬── col-3 ──┐
│  [Search bar + filtros tipo]                  │ Deadline  │
│  [Recent Artifacts — 3 cards inline]          │ Sensors   │
│  [Active Application Missions — tabla]        │           │
│                                               │ System    │
│                                               │ Status    │
└───────────────────────────────────────────────┴───────────┘
│  FAB: "Initiate New Application Sequence" (fixed bottom-right) │
```

**Componentes Core:**
- `<PortfolioTable>` — tabla con sticky header, filas clickeables, pipeline progress bar segmentado
- `<DeadlineSidebar>` — lista de deadlines con color coding urgency (error/amber/outline)
- `<RecentArtifacts>` — 3 cards de acceso rápido (CV, Cover Letter, JSON)
- `<SystemStatus>` — dot pulsando + uptime (decorativo, bottom del sidebar)
- `<SearchBar>` — input con filtros de tipo (CVs / Cover Letters / Job Postings / All)

**Componentes a Reciclar/Limpiar:**
- `PortfolioPage.tsx` existente — reescribir estructura completa con el nuevo layout
- `StageStatusBadge.tsx` — adaptar a la semántica de colores Terran Command
- `JobTree.tsx` — reemplazar con `<PortfolioTable>` (la tabla es más escaneable)

**Columnas de la tabla:**
```
Job_Title | Institution | Source | Pipeline_Stage (progress bar) | Status (badge)
```

**Pipeline_Stage progress bar** — segmentos de las 8 etapas: scrape, translate, extract, match, review_match, generate, render, package. Segmentos llenos = completados.

**Deadlines** — hand-crafted en el mock por ahora. En el futuro vendrán de un campo `deadline` en el job.

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Fondo general: `bg-surface` (`#121416`)
- Tabla header sticky: `bg-surface-container/95 backdrop-blur-sm`
- Filas hover: `hover:bg-primary/5`
- Sidebar deadlines: `alert-glow` (amber)
- Panel main: `tactical-glow` (cyan)

**Tipografía:**
- Nombre del app: `font-headline font-black uppercase tracking-tighter text-primary`
- Headers de sección (ACTIVE_APPLICATION_MISSIONS): `font-mono text-[11px] uppercase tracking-[0.2em] text-outline`
- Celdas: `font-mono text-[11px]`
- Job title en tabla: bold, `text-on-surface`

**Interacciones Clave:**
- Click en fila → navega a `/jobs/:source/:jobId`
- `Ctrl+K` → abre search bar (futura implementación)
- FAB hover → `brightness-110`, active → `scale-[0.98]`

**Estado Vacío:**
- Sin jobs: panel con `terminal` icon + "NO_ACTIVE_MISSIONS" en mono text

**Estado Error:**
- Si falla `getPortfolioSummary`: banner error en amber con mensaje mono

---

## Notas de Implementación

- Reemplaza completamente `PortfolioPage.tsx`
- La tabla debe ser scrollable internamente (`overflow-y-auto flex-1`) — no paginar
- El scanline overlay va sobre el `<main>` con `opacity-5`
- Los "Recent Artifacts" son estáticos por ahora (mock data) — no tienen endpoint propio todavía
- Los deadlines del sidebar vienen del mock `timeline_*.json` (campo `deadline` a añadir al mock)
