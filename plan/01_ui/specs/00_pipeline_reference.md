# Pipeline Reference: Flujo Completo PhD 2.0

Documento de referencia para el diseñador de UI. Describe cada etapa del pipeline con su propósito,
inputs/outputs, archivos involucrados, y si requiere HITL.

---

## Dos modos de ejecución

El código define dos configuraciones del grafo:

### PREP_MATCH (implementado y runnable hoy)
```
scrape → translate_if_needed → extract_understand → match → review_match
  → generate_documents → render → package
```

### DEFAULT (full pipeline — parcialmente implementado)
```
scrape → translate_if_needed → extract_understand → match → review_match
  → build_application_context → review_application_context
  → generate_motivation_letter → review_motivation_letter
  → tailor_cv → review_cv
  → draft_email → review_email
  → render → package
```

La diferencia clave: en PREP_MATCH, `generate_documents` hace en un solo paso lo que en DEFAULT
se divide en 3 nodos LLM separados (letter, cv, email), cada uno con su propia puerta HITL.

---

## Etapas — Ficha Completa

---

### 1. SCRAPE
**Estado:** Implementado ✅
**Tipo:** Determinista (tool-based — HTTP/Playwright)
**HITL:** No

**Objetivo:** Fetcha el job posting desde una URL. Normaliza el HTML a texto plano limpio.
Maneja JS-heavy sites con Playwright. Soporta adaptadores por fuente (Stepstone, TU Berlin, genérico).

**Input:**
- State: `source_url` (requerido), `source`, `job_id`
- Herramienta: `scrape_detail()` en `src/core/scraping/service.py`

**Output:**
- State key: `ingested_data` — dict con `source_url`, `original_language`, `raw_text`, `metadata`, `artifact_refs`, `warnings`
- Archivos escritos:
  - `nodes/scrape/input/raw_snapshot.json` — HTML crudo + metadata de fetch
  - `nodes/scrape/input/fetch_metadata.json` — URL, timestamp, HTTP status, adapter usado
  - `nodes/scrape/approved/canonical_scrape.json` — output normalizado
  - `nodes/scrape/proposed/source_extraction.json` — texto extraído pre-aprobación
  - `nodes/scrape/trace/error_screenshot.png` — solo si el scraper falló (Playwright screenshot)

**Archivos fuente clave:**
- `src/nodes/scrape/logic.py`
- `src/core/scraping/service.py`
- `src/core/scraping/fetchers/` — HTTP + Playwright fetchers

**Notas UI:** La vista de Scrape tiene dos modos: Setup (URL input) y Diagnóstico (output review).
El `error_screenshot.png` es clave para debugging — debe mostrarse prominentemente si existe.

---

### 2. TRANSLATE_IF_NEEDED
**Estado:** Implementado ✅
**Tipo:** Determinista (deep-translator — Google Translate backend)
**HITL:** No

**Objetivo:** Si el texto scrapeado no está en inglés, lo traduce al inglés en chunks de ≤4500 chars.
Si ya está en inglés, es un pass-through.

**Input:**
- State: `ingested_data` (requerido), `target_language` (default "en")
- Lee: `ingested_data.original_language` + `ingested_data.raw_text`

**Output:**
- State key: `ingested_data` (mutado — `raw_text` reemplazado por traducción)
- Agrega a metadata: `translated: true`, `translated_to: "en"`
- No escribe archivos propios — la modificación vive en state

**Archivos fuente clave:**
- `src/nodes/translate_if_needed/logic.py`
- `src/core/tools/translation/service.py`

**Notas UI:** No tiene vista propia. Debe aparecer como etapa en el Job Flow Inspector (con estado
completed/skipped). Si falló, mostrar el error. Sin interacción humana.

**Dudas abiertas:**
- ¿Cómo se distingue "completed" de "skipped" (texto ya en inglés)? ¿El artifact_ref existe o es null?

---

### 3. EXTRACT_UNDERSTAND
**Estado:** Implementado ✅
**Tipo:** LLM (Gemini — structured output con Pydantic schema)
**HITL:** No (pero el output sí es revisable en la UI — ver spec B2)

**Objetivo:** El LLM lee el texto crudo del job posting y extrae una representación estructurada:
requerimientos (must/nice), restricciones, areas de riesgo, info de contacto, salary grade.
Post-procesa enriqueciendo con spans de texto (posición en el markdown), emails por regex, salary por regex.

**Input:**
- State: `job_id`, `ingested_data.raw_text`
- Prompt template: `src/nodes/extract_understand/prompt/user_template.md`
- XML tags requeridos: `<job_posting_text>`

**Output Schema (`contract.py`):**
```python
JobUnderstandingExtract(
  job_title: str,
  analysis_notes: str,
  requirements: list[JobRequirement],   # id, text, priority (must/nice), text_span
  constraints: list[JobConstraint],     # constraint_type, description
  risk_areas: list[str],
  contact_info: ContactInfo,            # name, email (enriched post-LLM via regex)
  salary_grade: str                     # enriched post-LLM via regex
)
```

**State key:** `extracted_data`

**Archivos escritos:**
- `nodes/extract_understand/approved/state.json` — `JobUnderstandingExtract` serializado

**Archivos fuente clave:**
- `src/nodes/extract_understand/logic.py`
- `src/nodes/extract_understand/contract.py`
- `src/nodes/extract_understand/prompt/system.md`
- `src/nodes/extract_understand/prompt/user_template.md`

**Notas UI:** La vista de Extract (spec B2) permite al operador corregir, agregar o borrar requerimientos.
Aunque no hay gate HITL formal en el grafo actual, la UI debería permitir editar y guardar el state
antes de continuar al match.

---

### 4. MATCH
**Estado:** Implementado ✅
**Tipo:** LLM (Gemini — structured output) con loop de regeneración
**HITL:** No (pero su output va al review_match gate)

**Objetivo:** El LLM empareja cada requerimiento extraído con las evidencias del perfil del candidato.
Genera scores (0.0-1.0) y reasoning por requerimiento. Soporte de regeneración iterativa con feedback
de rondas previas.

**Input:**
- State: `job_id`, `extracted_data.requirements`, `my_profile_evidence`
- Contexto de regeneración (si aplica): `active_feedback`, `previous_round`, `regeneration_scope`
- Prompt XML tags: `<job_requirements>`, `<profile_evidence>`, `<feedback_rules>` (si regen)

**Output Schema (`contract.py`):**
```python
MatchEnvelope(
  matches: list[RequirementMatch],    # req_id, match_score (0-1), evidence_id, reasoning
  total_score: float,                 # 0.0-1.0
  decision_recommendation: Literal["proceed", "marginal", "reject"],
  summary_notes: str
)
```

**State key:** `matched_data`

**Archivos escritos:**
- `nodes/match/approved/state.json` — MatchEnvelope serializado
- `nodes/match/review/decision.md` — superficie de review para el operador (generada por review_match)

**Round management:** `src/core/round_manager.py`
- `nodes/match/review/rounds/round_NNN/decision.json`
- `nodes/match/review/rounds/round_NNN/feedback.json`

**Archivos fuente clave:**
- `src/nodes/match/logic.py`
- `src/nodes/match/contract.py`
- `src/nodes/match/prompt/system.md`, `user_template.md`
- `src/core/round_manager.py`

---

### 5. REVIEW_MATCH
**Estado:** Implementado ✅
**Tipo:** Determinista (parser de decisiones markdown)
**HITL:** Sí ⚡ — el grafo pausa aquí hasta que el operador edita `decision.md` y hace `--resume`

**Objetivo:** Genera la superficie de revisión en markdown (tabla de requerimientos con checkboxes),
pausa el grafo, y cuando se reanuda parsea la decisión del operador.

Soporta decisiones granulares por requerimiento o decisión global.

**Input:**
- State: `source`, `job_id`, `matched_data`
- Lee disco: `nodes/match/approved/state.json` (para validar hash de estado)

**Superficie de revisión generada (`decision.md`):**
```
| Req ID | Requirement | Evidence | Score | Reasoning | Action | Comments |
|--------|-------------|----------|-------|-----------|--------|----------|
| R001   | Python      | P_SKL_001| 0.9   | ...       | [x] Proceed / [ ] Regen / [ ] Reject | |
```

**Parsing de decisión:**
- Tabla por fila (preferido): si alguna fila tiene Reject → reject global; si alguna Regen → regen
- Fallback global: `Decision: [x] Proceed`
- Hash validation: `source_state_hash` previene aplicar feedback a output desactualizado
- `PATCH_EVIDENCE:` en Comments permite proponer nueva evidencia para el perfil

**Output:**
- State: `review_decision` (approve/request_regeneration/reject)
- State: `active_feedback` — lista de feedback patches para la siguiente regeneración de match
- Archivos:
  - `nodes/match/review/decision.json` — envelope parseado
  - `nodes/match/review/rounds/round_NNN/feedback.json` — feedback para regeneración

**Archivos fuente clave:**
- `src/nodes/review_match/logic.py`
- `src/core/tools/review_decision_service.py`

**Routing:**
- `approve` → `generate_documents`
- `request_regeneration` → `match` (con feedback context)
- `reject` → END

**Notas UI:** Actualmente el operador edita `decision.md` manualmente con cualquier editor.
La vista de Match (spec B3) debería reemplazar esto con una UI interactiva que genere el mismo
payload de decisión que el parser espera. El "COMMIT MATCH BUNDLE" del control panel debería
escribir al endpoint de saveEditorState.

---

### 6. BUILD_APPLICATION_CONTEXT
**Estado:** NO IMPLEMENTADO ⚠️ — Definido solo en graph.py
**Tipo:** Planeado LLM
**HITL:** No (pero su output va al review_application_context gate)

**Objetivo (inferido):** Construye el contexto narrativo del candidato para esta aplicación específica —
probablemente une el resultado del match con el perfil base para generar un "application brief"
que guíe la generación de los documentos individuales.

**Input esperado:** `matched_data`, `extracted_data`, perfil base
**Output esperado:** `application_context` — narrative brief por requerimiento / experiencia
**Archivos esperados:** `nodes/build_application_context/approved/state.json`

**Dudas abiertas:**
- ¿Qué estructura exacta tiene el `application_context`? ¿Es un dict por req_id → narrative?
- ¿Cuál es la diferencia con simplemente pasar `matched_data` directamente a `generate_documents`?
- ¿Este nodo se elimina en favor de mejorar el prompt de generate_documents?

---

### 7. REVIEW_APPLICATION_CONTEXT
**Estado:** NO IMPLEMENTADO ⚠️
**Tipo:** Determinista (parser similar a review_match)
**HITL:** Sí ⚡

**Objetivo (inferido):** Gate HITL para que el operador valide el contexto narrativo antes de
arrancar la generación de documentos. Permite refinar el framing antes de "gastar" tokens en
los 3 documentos completos.

**Routing esperado:**
- `approve` → `generate_motivation_letter`
- `request_regeneration` → `build_application_context`
- `reject` → END

**Dudas abiertas:**
- ¿Qué forma tiene la superficie de review? ¿Markdown tabla como review_match, o texto libre?
- ¿Este stage tiene sentido si build_application_context no está claro aún?

---

### 8. GENERATE_MOTIVATION_LETTER
**Estado:** NO IMPLEMENTADO ⚠️ — En DEFAULT pipeline, en PREP_MATCH está dentro de `generate_documents`
**Tipo:** Planeado LLM
**HITL:** No (su output va al review_motivation_letter gate)

**Objetivo:** Genera la motivation letter completa usando el application context y el perfil.
En PREP_MATCH esto se hace en `generate_documents` junto con CV y email en una sola llamada LLM.
En DEFAULT pipeline es una llamada LLM dedicada para mayor calidad y control.

**Input esperado:** `application_context`, `extracted_data`, perfil base
**Output esperado:** `motivation_letter` — texto completo de la carta
**Templates:** `src/nodes/generate_documents/templates/cover_letter_template.jinja2` (reutilizable)

**Dudas abiertas:**
- ¿El schema de output es `MotivationLetterDeltas` (como en PREP_MATCH) o texto completo directo?
- ¿Se reutiliza el assist determinista (forbidden phrases checker) de `generate_documents`?

---

### 9. REVIEW_MOTIVATION_LETTER
**Estado:** NO IMPLEMENTADO ⚠️
**Tipo:** Determinista (parser similar a review_match)
**HITL:** Sí ⚡

**Objetivo:** Gate HITL para aprobar/editar/pedir regeneración de la cover letter.

**Routing esperado:**
- `approve` → `tailor_cv`
- `request_regeneration` → `generate_motivation_letter`
- `reject` → END

**Notas UI:** Esta es la vista más rica para HITL C — el operador ve la carta generada, puede editarla
directamente, y la aprueba. Corresponde al tab "COVER_LETTER" del spec B4.

---

### 10. TAILOR_CV
**Estado:** NO IMPLEMENTADO ⚠️ — En PREP_MATCH está dentro de `generate_documents`
**Tipo:** Planeado LLM
**HITL:** No (su output va al review_cv gate)

**Objetivo:** Genera el CV adaptado: selecciona qué experiencias incluir, reordena bullets,
agrega bullets nuevos por experiencia según el match. En PREP_MATCH esto es `cv_injections`
dentro de `DocumentDeltas`.

**Input esperado:** `application_context`, perfil base CV, `matched_data`
**Output esperado:** `tailored_cv` — CV completo como markdown o como delta sobre el base
**Templates:** `src/nodes/generate_documents/templates/cv_template.jinja2` (reutilizable)

**Dudas abiertas:**
- ¿El output es un CV completo en markdown o son deltas (bullets a inyectar por experiencia)?
- ¿Cómo se aplican los deltas al base CV? ¿Jinja2 rendering o merge programático?

---

### 11. REVIEW_CV
**Estado:** NO IMPLEMENTADO ⚠️
**Tipo:** Determinista
**HITL:** Sí ⚡

**Objetivo:** Gate HITL para aprobar el CV adaptado. El operador lo edita y aprueba.

**Routing esperado:**
- `approve` → `draft_email`
- `request_regeneration` → `tailor_cv`
- `reject` → END

**Notas UI:** Tab "CV" del spec B4. El operador edita directamente en el Slate editor.

---

### 12. DRAFT_EMAIL
**Estado:** NO IMPLEMENTADO ⚠️ — En PREP_MATCH está dentro de `generate_documents`
**Tipo:** Planeado LLM
**HITL:** No (su output va al review_email gate)

**Objetivo:** Genera el email de aplicación (max 2 líneas según el assist checker actual).
En PREP_MATCH esto es `email_body` dentro de `DocumentDeltas`.

**Input esperado:** `application_context`, `extracted_data.contact_info`
**Output esperado:** `application_email` — texto del email con subject + body
**Templates:** `src/nodes/generate_documents/templates/email_template.jinja2` (reutilizable)

---

### 13. REVIEW_EMAIL
**Estado:** NO IMPLEMENTADO ⚠️
**Tipo:** Determinista
**HITL:** Sí ⚡

**Objetivo:** Gate HITL para aprobar el email de aplicación.

**Routing esperado:**
- `approve` → `render`
- `request_regeneration` → `draft_email`
- `reject` → END

**Notas UI:** Tab "EMAIL" del spec B4.

---

### 14. RENDER
**Estado:** Implementado ✅
**Tipo:** Determinista (copia + hash validation)
**HITL:** No

**Objetivo:** Copia los documentos de `generate_documents/proposed/` a `render/proposed/`
con validación de hashes sha256. Prepara los artefactos para el paso de packaging.

**Input:**
- Lee: `nodes/generate_documents/proposed/*.md`
- State: `source`, `job_id`

**Output Schema:**
```python
RenderStateEnvelope(
  documents: dict[str, RenderedDocumentRef]  # cv, motivation_letter, application_email
  # Cada ref: source_ref, rendered_ref, sha256
)
```

**State key:** `rendered_documents`

**Archivos escritos:**
- `nodes/render/proposed/cv.md`
- `nodes/render/proposed/motivation_letter.md`
- `nodes/render/proposed/application_email.md`
- `nodes/render/approved/state.json`

**Archivos fuente clave:**
- `src/nodes/render/logic.py`
- `src/nodes/render/contract.py`
- `src/core/io/provenance_service.py`

**Notas UI:** No tiene vista propia. Aparece como etapa completed en Job Flow Inspector.

**Dudas abiertas:**
- En el futuro ¿render hace compilación LaTeX del CV? ¿Cuándo se genera el PDF?
- ¿El "approved" de render requiere algún HITL gate? Actualmente no.

---

### 15. PACKAGE
**Estado:** Implementado ✅
**Tipo:** Determinista (finalizer)
**HITL:** No

**Objetivo:** Valida el render envelope, copia los documentos finales a `final/`, crea el manifest.
Marca el pipeline como completado.

**Input:**
- Lee: `nodes/render/approved/state.json`
- State: `source`, `job_id`

**Output Schema:**
```python
PackageManifest(
  artifacts: dict[str, PackagedArtifact],  # cv, motivation_letter, application_email
  # Cada artifact: path, sha256
  render_state_ref: str
)
```

**Archivos escritos:**
- `final/cv.md`
- `final/motivation_letter.md`
- `final/application_email.md`
- `final/manifest.json`

**State:** `status = "completed"`

**Archivos fuente clave:**
- `src/nodes/package/logic.py`
- `src/nodes/package/contract.py`

---

## Mapa de Herramientas Core

| Herramienta | Path | Función |
|-------------|------|---------|
| RoundManager | `src/core/round_manager.py` | Gestiona carpetas `rounds/round_NNN/` para iteración de feedback |
| ReviewDecisionService | `src/core/tools/review_decision_service.py` | Parsea checkboxes de decision.md → approve/regen/reject |
| WorkspaceManager | `src/core/io/workspace_manager.py` | Path resolution segura con validación de segmentos |
| ArtifactReader/Writer | `src/core/io/artifact_*.py` | Read/write de artefactos vía WorkspaceManager |
| ProvenanceService | `src/core/io/provenance_service.py` | sha256 hashing de artefactos |
| PromptManager | `src/ai/prompt_manager.py` | Jinja2 rendering de templates + XML tag validation |
| LLMRuntime | `src/ai/llm_runtime.py` | Wrapper Gemini con `generate_structured()` |
| ScrapingService | `src/core/scraping/service.py` | HTTP + Playwright fetching |
| TranslationService | `src/core/tools/translation/service.py` | deep-translator con chunking |

---

## Modelo de Error (Fail-Closed)

Todos los nodos deben fallar cerrado — ningún fallback silencioso. Tipos de error en `GraphState.ErrorContext`:

| Código | Causa |
|--------|-------|
| `MODEL_FAILURE` | LLM no retornó schema válido |
| `TOOL_FAILURE` | Scraper o translator falló |
| `IO_FAILURE` | Error de lectura/escritura en disco |
| `INPUT_MISSING` | State key requerido ausente |
| `SCHEMA_INVALID` | Pydantic validation falló |
| `POLICY_VIOLATION` | Violación de regla de negocio |
| `PARSER_REJECTED` | review_decision_service no pudo parsear |
| `REVIEW_LOCK_MISSING` | Hash de review no coincide |
| `INTERNAL_ERROR` | Error inesperado |

---

## Gaps UI vs. Pipeline — Resumen

| Etapa Pipeline | Tiene spec UI | Notas |
|----------------|---------------|-------|
| scrape | ✅ B1 | |
| translate_if_needed | Parcial | Solo en Job Flow Inspector como etapa — sin vista propia |
| extract_understand | ✅ B2 | |
| match | ✅ B3 | |
| review_match | ✅ B3 (integrado) | El review es parte de la vista match |
| build_application_context | ✅ B3b (especulativo) | Backend no implementado — spec listo |
| review_application_context | ✅ B3b (integrado) | Parte de la vista B3b |
| generate_motivation_letter | ✅ B4 (PREP_MATCH) + B4b (DEFAULT) | B4: 3 tabs simultáneos. B4b: 1 tab activo por gate |
| review_motivation_letter | ✅ B4b Gate C.1 | Tab "COVER_LETTER" |
| tailor_cv | ✅ B4b Gate C.2 | Tab "CV" |
| review_cv | ✅ B4b Gate C.2 | Tab "CV" |
| draft_email | ✅ B4b Gate C.3 | Tab "EMAIL" |
| review_email | ✅ B4b Gate C.3 | Tab "EMAIL" |
| render | En B0/B5 | Solo visible en Job Flow Inspector + Deployment |
| package | ✅ B5 | |

**Cobertura completa.** Todos los nodos del pipeline tienen spec UI. Los marcados como
⚠️ BLOCKED dependen del backend (B3b Fase 10, B4b Fase 8).
