# API Contract v2 — Review Workbench

> **Estado actual: MOCK** — El frontend consume `src/mock/client.ts` con datos estáticos.
> El backend real (`src/interfaces/api/`) existe pero implementa la API v1 con rutas distintas.
> Este documento describe el contrato v2 objetivo al que ambas capas deben converger.

---

## Principios de diseño

**CQRS Lite** — las rutas están separadas por intención:
- `/query/` — lectura pura, sin efectos secundarios. Hoy lee disco; mañana leerá Neo4j o MinIO.
- `/commands/` — escrituras y ejecución de flujos. Actúa sobre la CLI de Python por debajo.
- `/system/` — observabilidad e infraestructura (LangGraph, LangSmith, Neo4j, scrapers).

**Storage-agnostic** — el frontend no asume nada sobre el origen de los datos. Las shapes de respuesta son válidas independientemente de si la data viene de disco local, Neo4j, o MinIO.

**Versionado** — todas las rutas viven bajo `/api/v2/`. La v1 existente en `src/interfaces/api/` se considera legacy hasta que se migre.

---

## Base URL

```
http://127.0.0.1:8010   (configurable via VITE_REVIEW_API_BASE)
```

El switch mock/real no está implementado aún — el frontend siempre usa el mock. Cuando se active el backend real, bastará con apuntar las llamadas a `src/api/client.ts` en vez de `src/mock/client.ts`.

---

## 1. Capa de Consultas — `/api/v2/query/`

### Portfolio

| Método | Ruta | Respuesta |
|--------|------|-----------|
| `GET` | `/query/portfolio/summary` | `PortfolioSummary` |

`PortfolioSummary` incluye totales por status (`running`, `pending_hitl`, `completed`, `failed`, `archived`) y la lista de jobs con su estado actual.

### Perfil del candidato

| Método | Ruta | Respuesta |
|--------|------|-----------|
| `GET` | `/query/profile/base-cv-graph` | `BaseCvGraphPayload` |
| `GET` | `/query/profile/cv-profile-graph` | `CvProfileGraphPayload` |

- **`base-cv-graph`** — grafo estructural editable del CV base (vista A3).
- **`cv-profile-graph`** — grafo CV+perfil con `entries`, `skills`, `demonstrates`. Es el grafo que usa el motor de matching.

### Jobs

| Método | Ruta | Respuesta |
|--------|------|-----------|
| `GET` | `/query/jobs/:source/:job_id/timeline` | `JobTimeline` |
| `GET` | `/query/jobs/:source/:job_id/views/:view_name` | `ViewPayload` |
| `GET` | `/query/jobs/:source/:job_id/artifacts/:node_name` | `ArtifactListPayload` |
| `GET` | `/query/jobs/:source/:job_id/editor/:node_name/state` | `EditorState` |
| `GET` | `/query/jobs/:source/:job_id/evidence-bank` | `EvidenceBankPayload` |
| `GET` | `/query/jobs/:source/:job_id/profile/summary` | `ProfileSummary` |
| `GET` | `/query/jobs/:source/:job_id/package/files` | `PackageFilesPayload` |

#### `JobTimeline`

Devuelve el estado de todas las etapas del pipeline. El backend lo infiere de la presencia de archivos en disco (hoy) o del grafo de estado en Neo4j (futuro).

```ts
interface JobTimeline {
  source: string;
  job_id: string;
  thread_id: string;
  current_node: string;
  status: 'running' | 'pending_hitl' | 'completed' | 'failed' | 'archived';
  stages: {
    name: string;
    status: 'pending' | 'running' | 'needs_review' | 'approved' | 'error';
    artifact_ref: string | null;
    updated_at: string;
  }[];
  artifacts: Record<string, string>;
  updated_at: string;
}
```

#### `ViewPayload` — discriminated union

Un único endpoint paramétrico devuelve la data específica para cada vista de la UI. El discriminator `view` permite narrowing automático en TypeScript.

```ts
type ViewPayload =
  | { view: 'match';     source: string; job_id: string; data: MatchViewData }
  | { view: 'extract';   source: string; job_id: string; data: ExtractViewData }
  | { view: 'documents'; source: string; job_id: string; data: DocumentsViewData }
```

| `view` | `data` contiene | Vista UI |
|--------|-----------------|----------|
| `match` | `nodes[]`, `edges[]` (grafo requirement↔profile) | B3 Match |
| `extract` | `source_markdown`, `requirements[]` | B2 Extract |
| `documents` | `documents.{cv,motivation_letter,application_email}`, `nodes[]`, `edges[]` | B4 Docs |

#### `ArtifactListPayload`

Lista los archivos generados por un nodo específico. El contenido es texto inline (JSON formateado, markdown, o imagen en base64).

```ts
interface ArtifactListPayload {
  source: string;
  job_id: string;
  node_name: string;
  files: {
    path: string;
    content_type: 'json' | 'markdown' | 'text' | 'image' | 'binary' | 'too_large';
    content: string;
    editable: boolean;
  }[];
}
```

Archivos por nodo (backend real — `src/interfaces/api/read_models.py:_stage_relative_paths`):

| Nodo | Archivos expuestos |
|------|--------------------|
| `scrape` | `fetch_metadata.json`, `canonical_scrape.json`, `raw/source_text.md`, `error_screenshot.png` |
| `translate_if_needed` | `approved/state.json` |
| `extract_understand` | `approved/state.json` |
| `match` | `proposed/state.json`, `approved/state.json`, `review/decision.json` |
| `review_match` | `review/decision.json` |
| `generate_documents` | `approved/state.json`, `proposed/{cv,motivation_letter,application_email}.md`, `assist/proposed/view.md` |
| `render` | `approved/state.json`, `proposed/{cv,motivation_letter,application_email}.md` |
| `package` | `approved/state.json`, `final/manifest.json`, `final/{cv,motivation_letter,application_email}.md` |

### Explorer

| Método | Ruta | Respuesta |
|--------|------|-----------|
| `GET` | `/query/explorer/browse?path=` | `ExplorerPayload` |

Navega el filesystem de `data_root` (o MinIO en el futuro). Sin `path` devuelve la raíz. Para archivos, incluye el contenido inline si es previewable (≤512 KB).

---

## 2. Capa de Comandos — `/api/v2/commands/`

Toda mutación de estado y ejecución de pipeline pasa por esta capa. El backend ejecuta la CLI de Python por debajo.

### Jobs

| Método | Ruta | Body | Descripción |
|--------|------|------|-------------|
| `POST` | `/commands/jobs/scrape` | `{ url, source, adapter? }` | Lanza el scraper. Crea la carpeta del job. |
| `POST` | `/commands/jobs/:source/:job_id/run` | `{ target_node?, resume_from_hitl? }` | Inicia o reanuda LangGraph. **202 Accepted** — asíncrono. |
| `POST` | `/commands/jobs/:source/:job_id/gates/:gate_name/decide` | `{ decision, feedback? }` | Cierra un gate HITL. Escribe `decision.json` y despierta el thread. |
| `PUT` | `/commands/jobs/:source/:job_id/state/:node_name` | `{ ...state_data }` | Guarda borrador del estado editable de un nodo (extract, match). |
| `PUT` | `/commands/jobs/:source/:job_id/documents/:doc_key` | `{ markdown }` | Edita un documento generado (cv, motivation_letter, application_email). |
| `POST` | `/commands/jobs/:source/:job_id/archive` | `{ compress_to_minio }` | Empaqueta y limpia el job. |
| `DELETE` | `/commands/jobs/:source/:job_id` | — | Hard-delete de todo el rastro del job. |

#### Flujo HITL — cómo interactúa con la CLI

```
UI → PUT /commands/jobs/.../state/match         (guarda correcciones al JSON)
UI → POST /commands/jobs/.../gates/review_match/decide  { decision: "approve" }
      ↓ backend escribe decision.json
UI → POST /commands/jobs/.../run  { resume_from_hitl: true }
      ↓ backend ejecuta: python -m src.cli.run_prep_match --source X --job-id Y --resume
```

El `run` es siempre **asíncrono** — devuelve `{ run_id, status: "accepted" }` con HTTP 202. El frontend hace polling con `GET /system/orchestration/threads/:job_id` para saber cuándo terminó.

#### Gate decisions

```ts
type GateDecision = 'approve' | 'request_regeneration' | 'reject'

// Body de POST .../gates/:gate_name/decide
interface GateDecisionPayload {
  decision: GateDecision;
  feedback?: string[];   // solo para request_regeneration
}
```

Gates disponibles en el pipeline actual: `review_match`. En el DEFAULT pipeline futuro: `review_application_context`, `review_motivation_letter`, `review_cv`, `review_email`.

### Perfil

| Método | Ruta | Body | Descripción |
|--------|------|------|-------------|
| `PUT` | `/commands/profile/cv-profile-graph` | `CvProfileGraphPayload` | Guarda ediciones del grafo CV+perfil. |

### Explorer

| Método | Ruta | Body | Descripción |
|--------|------|------|-------------|
| `PUT` | `/commands/explorer/file?path=` | `{ content }` | Edición cruda de un archivo de texto. |

---

## 3. Capa de Sistema — `/api/v2/system/`

### Orquestación (LangGraph / LangSmith)

| Método | Ruta | Respuesta |
|--------|------|-----------|
| `GET` | `/system/orchestration/threads/:source/:job_id` | `ThreadStatus` |
| `GET` | `/system/orchestration/traces/:source/:job_id` | `TraceInfo` |

```ts
interface ThreadStatus {
  thread_id: string;
  is_active: boolean;
  current_node: string | null;
  pending_tasks: string[];
  last_updated: string;
}

interface TraceInfo {
  run_id: string;
  project_name: string;
  langsmith_url: string;   // link directo a la ejecución en LangSmith
  total_tokens: number;
  latency_ms: number;
}
```

### Scrapers

| Método | Ruta | Respuesta |
|--------|------|-----------|
| `GET` | `/system/scrapers/roadmap` | `ScraperRoadmap` |

Lista los adaptadores disponibles (`tu_berlin`, `stepstone`, `generic`), su estado de salud y capacidades (`js_rendering`, `playwright`, etc.).

### Neo4j

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/system/neo4j/health` | Check de conexión. |
| `POST` | `/system/neo4j/sync` | Fuerza sincronización de un job desde disco/MinIO hacia Neo4j. |

---

## 4. Archivos de código

```
apps/review-workbench/src/
  types/
    api.types.ts              ← tipos TypeScript del contrato completo

  api/
    client.ts                 ← cliente real (apunta a :8010/api/v2)

  mock/
    index.ts                  ← re-exporta apiClient
    client.ts                 ← cliente mock con ARTIFACTS lookup map
    fixtures/
      portfolio.json
      timeline_{jobId}.json                        (×2)
      view_{match|extract|documents}_{jobId}.json  (×6)
      artifacts_{node}_{jobId}.json                (×16, uno por nodo por job)
      cv_profile_graph.json
      editor_state_{jobId}.json                    (×2)
      evidence_bank.json
      explorer_root.json
      package_files_999001.json
      profile_summary.json
```

Backend real (v1 legacy, a migrar):
```
src/interfaces/api/
  app.py                  ← FastAPI entrypoint (:8010)
  config.py               ← settings via env vars (PHD2_DATA_ROOT, PHD2_NEO4J_URI, …)
  read_models.py          ← lógica de lectura del filesystem
  models.py               ← Pydantic models del dominio
  routers/
    portfolio.py          → /api/v1/portfolio/...
    jobs.py               → /api/v1/jobs/:source/:job_id/...
    explorer.py           → /api/v1/explorer/browse
    neo4j.py              → /api/v1/neo4j/...
    health.py             → /health
```

---

## 5. Datos de prueba del mock

Dos jobs ficticios bajo `source = "tu_berlin"`:

| `job_id` | Estado | Pipeline hasta |
|----------|--------|---------------|
| `201397` | `pending_hitl` en `review_match` | match aprobado, review pendiente, documentos vacíos |
| `999001` | `completed` | todos los nodos aprobados, 3 documentos finales disponibles |

El mock persiste cambios en memoria de sesión (`_docStore`, `_editorStore`). Al recargar la página, los datos vuelven al estado inicial de los fixtures.

---

## 6. Migración a Neo4j — qué cambia y qué no

| Capa | Cambio al migrar |
|------|-----------------|
| `/query/` | Sí — las funciones de `read_models.py` se reemplazan por queries Cypher. Los shapes de respuesta **no cambian**. |
| `/commands/` | No — siguen ejecutando la CLI y escribiendo a disco. Neo4j se actualiza vía `/system/neo4j/sync`. |
| `/system/neo4j/sync` | Se convierte en el punto de entrada del ETL disco → Neo4j. |
| Frontend | No — el `apiClient` es el mismo. Solo cambia de dónde vienen los datos. |

El schema de Neo4j está parcialmente definido en `src/interfaces/api/neo4j_schema.py` con constraints para: `Profile`, `Experience`, `Skill`, `Education`, `Language`, `JobPosting`, `Requirement`, `Application`, `TextSpan`, `SourceDocument`, y otros nodos del dominio.
