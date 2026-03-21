# Spec: Package & Deployment

## 1. Objetivo del Operador
El pipeline completó. El operador hace el checklist final y descarga el paquete de aplicación:
- Ver que todos los artefactos están en verde (rendered, packaged)
- Descargar los archivos finales (PDFs, docx, email MD)
- Marcar el job como "deployed" (enviado a la institución)
- Ver un resumen de misión: job title, institución, score, fecha

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/jobs/:source/:jobId/timeline` → `JobTimeline` (para checklist de stages)
- `GET /api/v1/jobs/:source/:jobId/package/files` → `PackageFilesPayload`
  ```ts
  {
    source, job_id,
    files: PackageFile[]    // { name, path, size_kb }
  }
  ```

**Escritura:** Ninguna desde la UI (el marking como deployed será CLI o futuro endpoint).

---

## 3. Composición de la UI y Layout

**Layout Base:** Columna central única (no split), centrada, max-width. Sin right panel.

```
┌─ LeftNav ─┬──────────────── Main (max-w-3xl centrado) ───────────────────────────────┐
│           │                                                                           │
│           │  [MISSION_COMPLETE header con glow]                                      │
│           │                                                                           │
│           │  ┌── Mission Summary card ──────────────────────────────────────────┐    │
│           │  │ Job: Research Assistant – TU Berlin         Score: 0.85          │    │
│           │  │ Thread: tu_berlin_999001              Completed: 2026-03-10      │    │
│           │  └──────────────────────────────────────────────────────────────────┘    │
│           │                                                                           │
│           │  ┌── Pipeline Checklist ────────────────────────────────────────────┐    │
│           │  │ [✓] SCRAPE            completed                                  │    │
│           │  │ [✓] EXTRACT           completed                                  │    │
│           │  │ [✓] MATCH             completed  score: 0.85                     │    │
│           │  │ [✓] REVIEW            approved                                   │    │
│           │  │ [✓] GENERATE          completed                                  │    │
│           │  │ [✓] RENDER            completed                                  │    │
│           │  │ [✓] PACKAGE           completed                                  │    │
│           │  └──────────────────────────────────────────────────────────────────┘    │
│           │                                                                           │
│           │  ┌── Package Files ─────────────────────────────────────────────────┐    │
│           │  │ [pdf icon] motivation_letter.pdf    84 KB   [download]           │    │
│           │  │ [pdf icon] cv.pdf                   62 KB   [download]           │    │
│           │  │ [md icon]  application_email.md      2 KB   [download]           │    │
│           │  │                                                                   │    │
│           │  │ [DOWNLOAD ALL AS ZIP]                                            │    │
│           │  └──────────────────────────────────────────────────────────────────┘    │
│           │                                                                           │
│           │  [MARK AS DEPLOYED →]  (prominent CTA, full width)                      │
└───────────┴───────────────────────────────────────────────────────────────────────────┘
```

**Componentes Core:**
- `<MissionSummaryCard>` — card con metadata del job y score
- `<PipelineChecklist>` — lista de etapas todas con ✓ (o ✗ si fallaron)
- `<PackageFileList>` — lista de archivos con iconos, tamaños y botones de descarga
- `<DeploymentCta>` — botón prominente full-width para marcar como deployed

**Componentes a Reciclar/Limpiar:**
- `DeploymentPage.tsx` — rediseñar completamente con este layout. Mantener lógica de fetch.

**Checklist item:**
```
[✓] STAGE_NAME    status_text    [artifact link opcional]
```
- Check verde: `text-primary` + `check_circle` icon filled
- Cross rojo: `text-error` + `cancel` icon (si alguna etapa falló)

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Fondo main: `bg-surface`
- Summary card: `bg-surface-container-low tactical-glow panel-border`
- Checklist container: `bg-surface-container-low panel-border`
- Package files container: `bg-surface-container-low panel-border`
- CTA Deployed: `bg-primary text-on-primary tactical-glow` — `hover:brightness-110`
- Header MISSION_COMPLETE: `text-primary drop-shadow-[0_0_12px_rgba(0,242,255,0.5)]`

**Tipografía:**
- Header: `font-headline font-black text-2xl uppercase tracking-tighter text-primary`
- Stage labels en checklist: `font-headline uppercase tracking-widest text-sm`
- Status text: `font-mono text-[10px] text-outline uppercase`
- File names: `font-mono text-xs text-on-surface`
- File sizes: `font-mono text-[10px] text-outline`
- Metadata (thread_id, score): `font-mono text-[10px]`

**Interacciones Clave:**
- Download individual → `<a href="/api/v1/jobs/:source/:jobId/package/files/:filename" download>`
- "Download All as ZIP" → endpoint futuro, por ahora disabled con tooltip `COMING_SOON`
- "Mark as Deployed" → confirm dialog → navega de vuelta al portfolio
- Click en artifact link del checklist → navega al Data Explorer en ese path

**Estado Vacío / Incompleto:**
- Si algunas etapas están pendientes (job no completado): checklist con items grises, CTA disabled
- Mensaje: `PIPELINE_INCOMPLETE — RETURN_TO_FLOW`

**Estado Error:**
- Si render/package fallaron: ítem con `✗` rojo + `ERROR_DETAILS` link al log
