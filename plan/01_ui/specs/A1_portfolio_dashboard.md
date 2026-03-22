# Spec A1 — Portfolio Dashboard

**Feature:** `src/features/portfolio/`
**Page:** `src/pages/global/PortfolioDashboard.tsx`
**Librerías:** `@tanstack/react-query` · `lucide-react` · `react-router-dom`
**Fase:** 0 (incluido en `phase_0_foundation`)

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/pages/` en branch `dev`  
**Legacy components:** extraer lógica de `PortfolioPage.tsx` si existe  
**To migrate:** extraer a `features/portfolio/` + aplicar estética Terran Command + conectar via `usePortfolioSummary`

---

## 1. Objetivo del Operador

Pantalla de inicio. El operador debe poder:
- Ver de un vistazo cuántos jobs están activos, en revisión, completados o fallidos
- Identificar cuál es el próximo job que requiere su atención (HITL bloqueado)
- Navegar a un job específico con un click
- Ver los deadlines más urgentes en el sidebar

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v2/query/portfolio/summary` → `PortfolioSummary`
  ```ts
  {
    totals: { jobs, completed, pending_hitl, running, failed, archived },
    jobs: JobListItem[]  // { source, job_id, thread_id, current_node, status, updated_at }
  }
  ```
  Status values: `running` · `pending_hitl` · `completed` · `failed` · `archived`

**Escritura:** Ninguna. Vista de solo lectura.

---

## 3. Composición de la UI y Layout

**Layout:** 12-col grid — `col-span-9` main + `col-span-3` sidebar derecho.

```
┌──────────────── col-9 ─────────────────┬── col-3 ──┐
│  [Search bar + filtros]                │ Deadline  │
│  [Recent Artifacts — 3 cards inline]  │ Sensors   │
│  [Active Application Missions — tabla] │           │
│                                        │ System    │
│                                        │ Status    │
└────────────────────────────────────────┴───────────┘
│  FAB: "Initiate New Application Sequence" (fixed bottom-right) │
```

**Componentes Core:**
- `<PortfolioTable>` — tabla sticky header, filas clickeables, pipeline progress bar segmentado
- `<DeadlineSidebar>` — lista de deadlines con color coding urgency (error/amber/outline)
- `<RecentArtifacts>` — 3 cards de acceso rápido (CV, Cover Letter, JSON)
- `<SystemStatus>` — dot pulsando + uptime (decorativo, bottom del sidebar)

**Columnas de la tabla:**
```
Job_Title | Institution | Source | Pipeline_Stage (progress bar) | Status (badge)
```

**Pipeline_Stage progress bar** — 8 segmentos: scrape, translate, extract, match, review, generate, render, package. Segmentos llenos = completados.

---

## 4. Estilos (Terran Command)

- Fondo: `bg-surface`
- Tabla header sticky: `bg-surface-container/95 backdrop-blur-sm`
- Filas hover: `hover:bg-primary/5`
- Sidebar deadlines: `alert-glow`
- Panel main: `tactical-glow`
- Nombre app: `font-headline font-black uppercase tracking-tighter text-primary`
- Headers sección: `font-mono text-[11px] uppercase tracking-[0.2em] text-outline`
- Celdas: `font-mono text-[11px]`

**Interacciones:**
- Click en fila → `navigate(/jobs/:source/:jobId)`
- `Ctrl+K` → abre search bar (futura implementación)
- FAB hover → `brightness-110`, active → `scale-[0.98]`

**Estado Vacío:** panel `terminal` icon + `NO_ACTIVE_MISSIONS`
**Estado Error:** banner amber mono si falla `getPortfolioSummary`

---

## 5. Archivos a crear

```
src/features/portfolio/
  api/
    usePortfolioSummary.ts        useQuery(['portfolio','summary'])
  components/
    PortfolioTable.tsx            tabla principal con Badge de status
    DeadlineSidebar.tsx           lista de deadlines
    RecentArtifacts.tsx           3 cards estáticos (mock data)
    SystemStatus.tsx              dot decorativo
src/pages/global/
  PortfolioDashboard.tsx          TONTO: useParams no necesario, solo hook + layout
src/components/atoms/
  Badge.tsx                       REQUERIDO por PortfolioTable (ya en phase_0)
```

---

## 6. Definition of Done

```
[ ] PortfolioDashboard renderiza sin errores de consola ni TS
[ ] Tabla muestra los 2 jobs del mock (201397, 999001)
[ ] Badge: pending_hitl=secondary(amber), completed=success, running=primary, failed=danger
[ ] Click en fila navega a /jobs/tu_berlin/201397
[ ] Estado vacío muestra NO_ACTIVE_MISSIONS si jobs=[]
[ ] Estado cargando muestra Spinner
[ ] Estado error muestra banner amber
[ ] DeadlineSidebar visible en col-3
[ ] RecentArtifacts muestra 3 cards (datos vienen del API/mock, no hardcodeados)
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/`

1. Verificar que `<PortfolioTable>` renderiza con al menos 2 filas
2. Verificar que la fila de job `201397` tiene Badge `pending_hitl`
3. Hacer click en la fila de `201397` → verificar navegación a `/jobs/tu_berlin/201397`
4. Volver a `/` → verificar que el sidebar derecho tiene sección de deadlines visible

---

## 8. Git Workflow

### Commit al cerrar la fase

```
feat(ui): implement portfolio dashboard (A1)

- PortfolioTable with job list and status badges
- DeadlineSidebar with urgency color coding
- RecentArtifacts 3-card panel
- SystemStatus decorative component
- Connected to usePortfolioSummary hook
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented A1 Portfolio Dashboard: job list table with status badges,
  deadline sidebar, recent artifacts panel, and system status indicator.
```

### Checklist update (index_checklist.md)

- [x] A1 Portfolio Dashboard
