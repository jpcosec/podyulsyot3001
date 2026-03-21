# Spec: Scrape (Setup / Diagnóstico)

## 1. Objetivo del Operador
Esta vista tiene dos modos según el estado del job:

**Modo Setup (job nuevo):** El operador configura la URL a scrapear y elige el adaptador de fuente. Lanza el scrape.

**Modo Diagnóstico (scrape ya ejecutado):** El operador revisa el resultado — texto extraído, metadata, y si falló: el screenshot de error del scraper. Puede re-lanzar el scrape si el resultado es incompleto.

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/jobs/:source/:jobId/stage/scrape/outputs` → `StageOutputsPayload`
  ```ts
  {
    source, job_id, stage: "scrape", node_name: "scrape",
    files: StageOutputFile[]   // canonical_scrape.json, raw.html, error_screenshot.png, etc.
  }
  ```

**Escritura (Setup mode):**
- `POST /api/v1/jobs` → `{ source_url, source, job_id?, adapter }` (futura — no implementado aún)
- Por ahora en el mock, modo diagnóstico solamente.

---

## 3. Composición de la UI y Layout

**Layout Base:** Columna única con cards verticales (no split). Right panel con control actions.

```
┌─ LeftNav ─┬────────────── Main ─────────────────────────────┬── Control Panel ──┐
│           │  [SCRAPE_DIAGNOSTICS header]                    │ [PHASE: SCRAPE]   │
│           │                                                 │                   │
│           │  ┌── Fetch Metadata card ───────────────────┐  │ URL configurada   │
│           │  │ URL: https://jobs.tu-berlin.de/...       │  │ Adapter: tu_berlin│
│           │  │ Retrieved: 2026-03-05T04:50:18Z          │  │ Status: completed │
│           │  │ Adapter: tu_berlin                       │  │                   │
│           │  │ HTTP Status: 200                         │  │ [RE-RUN SCRAPE]   │
│           │  └──────────────────────────────────────────┘  │                   │
│           │                                                 │ [ADVANCE →]       │
│           │  ┌── Source Text Preview ───────────────────┐  │                   │
│           │  │ [texto extraído — 20 líneas con scroll]  │  │                   │
│           │  │ [expand button]                          │  │                   │
│           │  └──────────────────────────────────────────┘  │                   │
│           │                                                 │                   │
│           │  ┌── Error Screenshot (si existe) ──────────┐  │                   │
│           │  │ [img screenshot]  ERROR_TRACE: ...       │  │                   │
│           │  └──────────────────────────────────────────┘  │                   │
└───────────┴─────────────────────────────────────────────────┴───────────────────┘
```

**Componentes Core:**
- `<ScrapeMetaCard>` — URL, timestamp, adapter, HTTP status
- `<SourceTextPreview>` — texto colapsable (20 líneas → expand full)
- `<ErrorScreenshot>` — imagen inline si existe `error_screenshot.png` en los outputs
- `<ScrapeControlPanel>` — right panel con re-run + advance actions

**Componentes a Reciclar/Limpiar:**
- `PipelineOutputsView.tsx` — sirve de base para mostrar los artefactos de scrape
- No hay vista actual específica de scrape — es nueva

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Cards de metadata: `bg-surface-container-low panel-border`
- Source text preview: `bg-surface-container-lowest border border-outline-variant/20 font-mono text-xs`
- Error screenshot container: `border border-error/40 bg-error-container/10`
- HTTP 200 status: `text-primary font-mono`
- HTTP 4xx/5xx status: `text-error font-mono`

**Tipografía:**
- Headers de card: `font-mono text-[10px] text-outline uppercase tracking-[0.2em]`
- Valores de metadata: `font-mono text-xs text-on-surface`
- Source text: `font-mono text-xs text-on-surface-variant leading-relaxed`

**Interacciones Clave:**
- "RE-RUN SCRAPE" → confirm dialog + re-dispara el nodo (endpoint futuro)
- "ADVANCE" → navega a Extract & Understand
- "EXPAND" en source text → modal o inline expand del contenido completo

**Estado Vacío:**
- Scrape aún no ejecutado (setup mode): form con input de URL + selector de adaptador + botón LAUNCH
- No hay screenshot de error: sección oculta

**Estado Error:**
- Scrape falló: banner rojo `SCRAPE_FAILED` + screenshot de error prominente
- Texto extraído vacío: warning `EMPTY_CONTENT_EXTRACTED — REVIEW_SCREENSHOT`
