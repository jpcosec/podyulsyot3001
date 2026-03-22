# Spec B1 — Scrape Diagnostics

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/ScrapeDiagnostics.tsx`
**Librerías:** `@tanstack/react-query` · `lucide-react`
**Fase:** 3

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/views/` en branch `dev`  
**To migrate:** extraer lógica de scrape outputs a `features/job-pipeline/` + aplicar estética Terran Command + conectar via `useArtifacts`

Dos modos según el estado del job:

**Modo Setup (job nuevo):** Configura la URL a scrapear y elige el adaptador. Lanza el scrape.

**Modo Diagnóstico (scrape ejecutado):** Revisa el resultado — texto extraído, metadata HTTP, y si falló: el screenshot de error. Puede re-lanzar el scrape si el resultado es incompleto.

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v2/query/jobs/:source/:job_id/artifacts/scrape` → `ArtifactListPayload`
  ```ts
  {
    source, job_id, node_name: "scrape",
    files: { path, content_type, content, editable }[]
    // paths: fetch_metadata.json · canonical_scrape.json · raw/source_text.md · error_screenshot.png
  }
  ```

**Escritura (Setup mode):**
- `POST /api/v2/commands/jobs/scrape` → `{ url, source, adapter? }` (**futuro — no implementado**)
- Por ahora: modo diagnóstico solamente con datos del mock.

---

## 3. Composición de la UI y Layout

**Layout:** Columna única con cards + right control panel.

```
┌──────────────── Main ─────────────────────┬── Control Panel ──┐
│  [SCRAPE_DIAGNOSTICS header]              │ [PHASE: SCRAPE]   │
│                                           │                   │
│  ┌── Fetch Metadata ──────────────────┐  │ URL configurada   │
│  │ URL: https://...                   │  │ Adapter: tu_berlin│
│  │ Retrieved: 2026-03-05T04:50:18Z   │  │ Status: completed │
│  │ Adapter: tu_berlin  HTTP: 200      │  │                   │
│  └────────────────────────────────────┘  │ [RE-RUN SCRAPE]   │
│                                           │ [ADVANCE →]       │
│  ┌── Source Text Preview ─────────────┐  │                   │
│  │ [20 líneas collapsable]            │  │                   │
│  │ [EXPAND button]                    │  │                   │
│  └────────────────────────────────────┘  │                   │
│                                           │                   │
│  ┌── Error Screenshot (si existe) ────┐  │                   │
│  │ [img] ERROR_TRACE: ...             │  │                   │
│  └────────────────────────────────────┘  │                   │
└───────────────────────────────────────────┴───────────────────┘
```

**Componentes Core:**
- `<ScrapeMetaCard>` — URL, timestamp, adapter, HTTP status
- `<SourceTextPreview>` — texto colapsable (20 líneas → expand full)
- `<ErrorScreenshot>` — imagen inline si existe `error_screenshot.png`
- `<ScrapeControlPanel>` — re-run + advance actions

---

## 4. Estilos (Terran Command)

- Cards: `bg-surface-container-low panel-border`
- Source text: `bg-surface-low border border-outline/20 font-mono text-xs`
- Error screenshot container: `border border-error/40 bg-error-container/10`
- HTTP 200: `text-primary font-mono`
- HTTP 4xx/5xx: `text-error font-mono`
- Card headers: `font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]`

**Interacciones:**
- "RE-RUN SCRAPE" → confirm dialog (endpoint futuro — disabled en mock)
- "ADVANCE" → navega a `/extract`
- "EXPAND" en source text → modal o inline expand

**Estado Setup (sin scrape):** form con input URL + selector adaptador + botón LAUNCH
**Estado Error:** banner rojo `SCRAPE_FAILED` + screenshot prominente

---

## 5. Archivos a crear

```
src/features/job-pipeline/
  api/
    useArtifacts.ts               useQuery(['artifacts', source, jobId, 'scrape'])
  components/
    ScrapeMetaCard.tsx            URL, timestamp, HTTP status
    SourceTextPreview.tsx         texto colapsable
    ErrorScreenshot.tsx           imagen condicional
    ScrapeControlPanel.tsx        re-run + advance
src/pages/job/
  ScrapeDiagnostics.tsx           TONTO: useParams + hook + render
```

---

## 6. Definition of Done

```
[ ] ScrapeDiagnostics renderiza sin errores para job 201397 (mock)
[ ] ScrapeMetaCard muestra URL, timestamp, adapter, HTTP status del mock
[ ] SourceTextPreview muestra las primeras 20 líneas colapsado
[ ] EXPAND muestra el texto completo
[ ] ErrorScreenshot no aparece si no hay error en los outputs del mock
[ ] "ADVANCE" navega a /jobs/tu_berlin/201397/extract
[ ] Estado loading muestra Spinner
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/201397/scrape`

1. Verificar que `<ScrapeMetaCard>` renderiza con URL y HTTP status visibles
2. Verificar que `<SourceTextPreview>` está colapsado (máx 20 líneas)
3. Click en EXPAND → verificar que el texto completo es visible
4. Click en ADVANCE → verificar navegación a `/jobs/tu_berlin/201397/extract`

---

## 8. Git Workflow

### Commit al cerrar la fase

```
feat(ui): implement scrape diagnostics (B1)

- ScrapeMetaCard with URL, timestamp, adapter, HTTP status
- SourceTextPreview with collapsible text
- ErrorScreenshot conditional display
- ScrapeControlPanel with re-run and advance actions
- Connected to useArtifacts hook
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented B1 Scrape Diagnostics: metadata card, collapsible source text preview,
  error screenshot display, and scrape control panel.
```

### Checklist update (index_checklist.md)

- [x] B1 Scrape Diagnostics
