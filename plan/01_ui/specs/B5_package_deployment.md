# Spec B5 — Package & Deployment

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/PackageDeployment.tsx`
**Librerías:** `@tanstack/react-query` · `lucide-react`
**Fase:** 7

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/` en branch `dev`  
**Legacy reference:** extraer lógica de deployment de pages existentes  
**To migrate:** crear `features/job-pipeline/` components + conectar via `usePackageFiles`

El pipeline completó. El operador hace el checklist final y descarga el paquete:
- Verificar que todos los artefactos están en verde (rendered, packaged)
- Descargar los archivos finales (PDFs, email MD)
- Marcar el job como "deployed" (enviado a la institución)
- Ver un resumen de misión: job title, institución, score, fecha

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v2/query/jobs/:source/:job_id/timeline` → `JobTimeline` (para checklist de stages)
- `GET /api/v2/query/jobs/:source/:job_id/package/files` → `PackageFilesPayload`
  ```ts
  {
    source, job_id,
    files: PackageFile[]   // { name, path, size_kb }
  }
  ```

**Escritura:**
- `POST /api/v2/commands/jobs/:source/:job_id/archive` — futuro: marca como deployed + comprime

---

## 3. Composición de la UI y Layout

**Layout:** Columna central única, max-w-3xl, centrada.

```
┌──────── Main (max-w-3xl centrado) ─────────────────────────────┐
│                                                                  │
│  [MISSION_COMPLETE header — glow cyan]                          │
│                                                                  │
│  ┌── Mission Summary ─────────────────────────────────────┐    │
│  │ Job: Research Assistant – TU Berlin   Score: 0.85      │    │
│  │ Thread: tu_berlin_999001    Completed: 2026-03-10      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── Pipeline Checklist ──────────────────────────────────┐    │
│  │ [✓] SCRAPE         completed                           │    │
│  │ [✓] EXTRACT        completed                           │    │
│  │ [✓] MATCH          completed  score: 0.85              │    │
│  │ [✓] REVIEW         approved                            │    │
│  │ [✓] GENERATE       completed                           │    │
│  │ [✓] RENDER         completed                           │    │
│  │ [✓] PACKAGE        completed                           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌── Package Files ───────────────────────────────────────┐    │
│  │ [FileType] motivation_letter.pdf   84 KB  [download]   │    │
│  │ [FileType] cv.pdf                  62 KB  [download]   │    │
│  │ [FileText] application_email.md     2 KB  [download]   │    │
│  │ [DOWNLOAD ALL AS ZIP — disabled, COMING_SOON]          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [MARK AS DEPLOYED →]  (full-width CTA, bg-primary)            │
└──────────────────────────────────────────────────────────────────┘
```

**Componentes Core:**
- `<MissionSummaryCard>` — metadata del job y score
- `<PipelineChecklist>` — lista de etapas todas ✓ (o ✗ si fallaron)
- `<PackageFileList>` — archivos con iconos, tamaños y botones download
- `<DeploymentCta>` — botón full-width prominente

**Checklist item:**
```
[✓] STAGE_NAME    status_text    [artifact link]
check verde: text-primary + CheckCircle icon
cross rojo:  text-error + XCircle icon
```

---

## 4. Estilos (Terran Command)

- Header `MISSION_COMPLETE`: `font-headline font-black text-2xl uppercase tracking-tighter text-primary drop-shadow-[0_0_12px_rgba(0,242,255,0.5)]`
- Summary card: `bg-surface-low tactical-glow panel-border`
- Checklist container: `bg-surface-low panel-border`
- Package files container: `bg-surface-low panel-border`
- CTA Deployed: `bg-primary text-primary-on tactical-glow hover:brightness-110`
- Stage labels: `font-headline uppercase tracking-widest text-sm`
- File names: `font-mono text-xs text-on-surface`
- Metadata: `font-mono text-[10px]`

**Interacciones:**
- Download individual → `<a href="..." download>`
- "Download All as ZIP" → disabled, tooltip `COMING_SOON`
- "MARK AS DEPLOYED" → confirm dialog → navega al portfolio

**Estado Incompleto:** checklist con ítems grises, CTA disabled con `PIPELINE_INCOMPLETE — RETURN_TO_FLOW`
**Estado Error:** ítem ✗ rojo con link a log de error

---

## 5. Archivos a crear

```
src/features/job-pipeline/
  api/
    usePackageFiles.ts            useQuery(['package-files', source, jobId])
    (reutiliza useJobTimeline.ts de B0)
  components/
    MissionSummaryCard.tsx        metadata del job
    PipelineChecklist.tsx         lista de stages con ✓/✗
    PackageFileList.tsx           archivos con download links
    DeploymentCta.tsx             botón full-width
src/pages/job/
  PackageDeployment.tsx           TONTO: useParams + hooks + render
```

---

## 6. Definition of Done

```
[ ] PackageDeployment renderiza sin errores para job 999001 (mock)
[ ] MissionSummaryCard muestra título, score y fecha del mock
[ ] PipelineChecklist muestra todas las etapas con ✓ verde
[ ] PackageFileList muestra los 3 archivos del mock con tamaños
[ ] Links de download tienen href correctos
[ ] "DOWNLOAD ALL AS ZIP" aparece disabled con tooltip COMING_SOON
[ ] "MARK AS DEPLOYED" abre confirm dialog
[ ] Confirm → navega a /
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/999001/sculpt` (o ruta de deployment si se agrega)

1. Verificar que `MISSION_COMPLETE` header es visible con glow cyan
2. Verificar que `<PipelineChecklist>` muestra 7 items con checkmarks verdes
3. Verificar que `<PackageFileList>` muestra 3 archivos con botones de download
4. Click en "MARK AS DEPLOYED" → verificar que aparece confirm dialog
5. Confirmar → verificar navegación a `/`

---

## 8. Git Workflow

### Commit al cerrar la fase

```
feat(ui): implement package & deployment (B5)

- MissionSummaryCard with job metadata and score
- PipelineChecklist with stage completion indicators
- PackageFileList with download buttons
- DeploymentCta full-width button
- Connected to usePackageFiles hook
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented B5 Package & Deployment: mission summary, pipeline checklist,
  downloadable package files, and deployment CTA.
```

### Checklist update (index_checklist.md)

- [x] B5 Package & Deployment
