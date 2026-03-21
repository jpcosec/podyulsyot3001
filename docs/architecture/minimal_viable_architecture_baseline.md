# PhD 2.0 Minimal Viable Architecture Completion Plan

## Contexto

PhD 2.0 se esta reorientando desde una vision mas pesada y futura hacia una arquitectura minima viable que permita dos cosas cuanto antes:

1. estabilizar el pipeline LLM
2. hacer review humana rapida sobre artefactos locales reales

La prioridad no es Neo4j ni una UI final de conocimiento global. La prioridad es trabajar sobre los JSON reales que ya viven en `data/jobs/<source>/<job_id>/` y cerrar un flujo util de inspeccion, correccion y guardado para las etapas que hoy importan.

Las fuentes de verdad para este plan son:

- `plan/01_ui/fase1_minimal_json_editor.md`
- `plan/02_langchain/fase1_llm_wrappers_y_structured_output.md`
- `plan/03_scrapper/phase1_scraping_and_autoapply.md`
- `plan/index_checklist.md`

## Objetivo

Completar la arquitectura minima viable con estos resultados concretos:

1. UI usable sobre archivos JSON locales para inspeccionar outputs por etapa y editar `extract_understand`, `match` y documentos generados.
2. `extract_understand` estabilizado con LangChain wrappers y structured output sin tocar `src/graph.py`.
3. LangSmith conectado para tener seguimiento auditable del pipeline y de las etapas LLM prioritarias.
4. scraping robusto con evidencia visual en fallos, perfil persistente para navegador, y cascada completa auditable sin introducir complejidad enterprise innecesaria.

## Restricciones no negociables

1. Cero Neo4j como formato de trabajo actual.
2. La fuente de verdad es `data/jobs/`.
3. El backend solo expone read/write directo sobre artefactos locales.
4. LangChain se usa solo en la capa LLM, no para reescribir la orquestacion.
5. Los TextSpans deben resolverse por matching determinista, nunca por offsets inventados por el LLM.
6. Si falta una libreria necesaria para cerrar el minimal, se instala en esta fase.

## Aclaracion clave: que significa TextSpan determinista

En esta fase no queremos que el LLM devuelva posiciones exactas dentro del texto, como `start_offset` o `end_offset`, porque esos offsets suelen ser inconsistentes o directamente inventados.

Lo que si aceptamos es que el modelo devuelva una cita verificable, por ejemplo `exact_quote`.

Luego el backend o la UI calculan la posicion real sobre el texto fuente local con reglas reproducibles:

1. leer el texto fuente guardado en disco
2. buscar la cita dentro de ese texto
3. si aparece, derivar lineas, snippet o posicion real
4. si no aparece, devolver `not found` y no inventar un span

Ejemplo:

- el modelo devuelve `exact_quote = "TV-L E13"`
- la UI o backend busca `TV-L E13` en `source_text.md`
- si lo encuentra, usa esa coincidencia real para highlight o linking
- si no lo encuentra, no crea offsets falsos

Esto hace que el linking entre texto fuente y evidencia sea auditable y repetible.

## Alcance

### Track 1: UI minimal

- reusar y terminar el `NodeEditor` ya existente como superficie HITL principal
- inspeccion por etapa del pipeline
- editor JSON-backed para `extract_understand`
- editor JSON-backed para `match`
- edicion final de documentos de `generate_documents`
- navegacion coherente desde la pagina del job
- lista completa y concreta de superficies UI involucradas

### Track 2: AI minimal

- `extract_understand` con `ChatGoogleGenerativeAI`
- `with_structured_output()` contra schema estricto
- conexion de LangSmith para trazabilidad de etapas y prompts
- `contact_info` fiable
- `salary_grade` opcional y nunca fatal
- eliminacion de offsets LLM

### Track 3: Scrapper minimal

- `PlaywrightFetcher` con `try/except`
- guardado de `error_screenshot.png`
- uso de `bot_profile` persistente
- cascada HTTP -> Playwright -> LLM fallback como ruta necesaria
- visibilidad clara en UI/API de como se hizo cada scraping y si esta funcionando

## Que no hacer

1. No mover persistencia a Neo4j.
2. No redisenar la UI completa antes de cerrar los minimals.
3. No reescribir `src/graph.py` ni el routing LangGraph.
4. No pedir offsets al LLM.
5. No introducir una capa de abstraccion nueva que esconda `data/jobs/`.
6. No convertir esta fase en una migracion full-pipeline a LangChain.
7. No expandir auto-apply hasta que el scraping baseline quede robusto.
8. No crear un editor paralelo si el `NodeEditor` actual ya puede cubrir la necesidad con vistas y schemas nuevos.

## Librerias y templates a usar

### Backend / pipeline

- FastAPI para endpoints de lectura y escritura directa.
- Pydantic para contratos y validacion.
- `WorkspaceManager` y `ArtifactWriter` para acceso seguro a artefactos locales.

### AI

- `langchain-google-genai`
- `langchain-core`
- `langsmith`
- `ChatPromptTemplate`
- `ChatGoogleGenerativeAI`
- `.with_structured_output()`

### Frontend

- React
- `NodeEditor` existente como base de la UI HITL
- fetch API existente en `apps/review-workbench/src/api/client.ts`

### Prompts y templates

- mantener `system.md`
- mantener `user_template.md`
- envolver prompts existentes, no duplicarlos ni reescribir la disciplina de prompts

## Plan de trabajo

### Step 0 - Cerrar inventario y spec minima de UI

#### Objetivo

Confirmar que existe una lista completa de las superficies UI del minimal y como se van a ver antes de seguir agregando piezas sueltas.

#### Tareas

1. Enumerar todas las superficies UI involucradas en el minimal.
2. Confirmar cual de ellas reusa `NodeEditor`, cual reusa views existentes y cual necesita solo schema/adaptador nuevo.
3. Confirmar flujos exactos de operador por etapa.
4. Si falta una lista cerrada o un comportamiento no esta claro, detener implementacion y pedirle al usuario la spec faltante.

#### Lista minima que debe quedar cerrada

1. Job page como hub de navegacion.
2. Vista de outputs por stage.
3. `NodeEditor` para `extract_understand`.
4. `NodeEditor` para `match`.
5. Vista/editor de documentos para `generate_documents`.
6. Vista de scraping con modo usado, warnings, artifacts y screenshot si existe.

#### Gate

No seguir implementando UI si esta lista no esta cerrada y comprensible.

Este Step 0 es prerrequisito para todo el track UI.

### Fase A - Cerrar el puente UI <-> JSON local

#### Objetivo

Que cada job tenga una superficie clara para ver y editar los outputs relevantes del pipeline usando solo archivos locales.

#### Tareas

1. Consolidar la vista `Pipeline Outputs` como superficie principal de inspeccion por etapa.
2. Reusar el `NodeEditor` existente para `extract_understand` con affordances mas guiadas para campos clave.
3. Reusar el `NodeEditor` existente para `match` con affordances para score, reasoning y evidence links.
4. Agregar edicion y guardado de documentos de `generate_documents` desde la UI.
5. Mantener compatibilidad con el rumbo futuro: misma navegacion por job y por stage, pero sobre JSON local.

#### Pseudocodigo

```text
GET /jobs/{source}/{job_id}/stage/{stage}/outputs
  -> leer lista conocida de artefactos esperados por stage
  -> devolver solo archivos existentes

GET /jobs/{source}/{job_id}/editor/{node}/state
  -> leer nodes/<node>/approved/state.json

PUT /jobs/{source}/{job_id}/editor/{node}/state
  -> validar payload JSON
  -> sobrescribir state.json de forma atomica

GET /jobs/{source}/{job_id}/documents/{doc_key}
PUT /jobs/{source}/{job_id}/documents/{doc_key}
  -> leer/escribir markdown o JSON final de generate_documents
```

### Fase B - Endurecer `extract_understand`

#### Objetivo

Que la extraccion estructurada sea estable y util en los campos mas sensibles para review humana.

#### Tareas

1. Mantener `ChatGoogleGenerativeAI` y `with_structured_output()` como camino oficial.
2. Endurecer el schema con `contact_info` y `salary_grade: Optional[str]`.
3. Priorizar fiabilidad de PI/contacto y email.
4. Mantener `salary_grade` como null si no existe.
5. Mover TextSpan hacia `exact_quote` + resolucion determinista posterior.
6. Conectar LangSmith para trazabilidad de prompts, respuestas y errores.
7. Agregar casos de prueba con postings reales guardados localmente.
8. Instalar librerias faltantes si el runtime aun no las tiene.

#### Pseudocodigo

```text
run_logic(state)
  -> build prompt from current templates
  -> call ChatGoogleGenerativeAI.with_structured_output(schema)
  -> emit trace to LangSmith
  -> validate result
  -> enrich contact/salary only with deterministic post-processing if needed
  -> persist extracted_data compatible with current downstream consumers
```

### Fase C - Cerrar review determinista de evidencia

#### Objetivo

Que la UI pueda vincular requirement/evidence/source text sin offsets alucinados.

#### Tareas

1. Definir una utilidad comun de busqueda de texto por `exact_quote`.
2. Resolver linea, offset o fragmento visible desde texto fuente real.
3. Reusar esa resolucion en `View 2` y en el editor del job.
4. Mantener compatibilidad con una futura UI mas rica, pero sin depender de ella.

#### Explicacion operativa

Aqui `matching determinista` significa que el enlace entre evidencia y texto fuente se calcula con reglas reproducibles sobre el texto guardado en disco, no con posiciones estimadas por el modelo.

Ejemplos aceptables:

1. busqueda exacta de substring
2. busqueda normalizada ignorando espacios redundantes
3. derivacion de lineas a partir de una coincidencia encontrada

Ejemplos no aceptables:

1. pedirle al LLM `start_offset` y `end_offset`
2. inventar lineas si la cita no aparece
3. guardar spans que no puedan recalcularse desde el texto local

#### Pseudocodigo

```text
resolve_span(source_text, exact_quote)
  -> normalize source_text
  -> normalize exact_quote
  -> find first deterministic match
  -> derive line range and preview snippet
  -> return null if not found, never invent
```

### Fase D - Terminar el scraping minimal

#### Objetivo

Que el scraping sea suficientemente robusto para no dejar ciego al operador cuando una pagina JS falle.

#### Tareas

1. Verificar que `PlaywrightFetcher` siempre capture screenshot en fallo cuando exista job context.
2. Verificar que `bot_profile` persistente sea el default operacional documentado.
3. Endurecer la cascada HTTP -> Playwright -> LLM fallback.
4. Hacer visible en artifacts y UI que modo se uso, que fallo, y que warnings hubo.
5. Mantener artefactos en `nodes/scrape/` y `raw/source_text.md`.
6. Exponer una vista clara para revisar cada scraping y diagnosticar si esta funcionando.

#### Pseudocodigo

```text
scrape_detail(request)
  -> try http fetch
  -> if missing/blocked/failed then try playwright fetch
  -> on playwright exception save error_screenshot.png in trace/
  -> if deterministic extraction still fails escalate to LLM fallback
  -> persist fetch_metadata/raw_snapshot/source_extraction/canonical_scrape
```

### Fase E - Cerrar la experiencia minima de operador

#### Objetivo

Que el operador pueda recorrer el pipeline de un job sin salir de la superficie de trabajo minima.

#### Tareas

1. Desde la job page: ver timeline, elegir stage, inspeccionar outputs.
2. Editar `extract_understand` y `match` desde el editor.
3. Editar documentos finales desde UI.
4. Ver feedback suficiente para saber que se guardo en disco.
5. Mantener comandos CLI solo como complemento, no como unica forma de revisar.

## Cuando considerar terminado

El plan minimal puede considerarse terminado cuando se cumplan todas estas condiciones:

1. `extract_understand` y `match` se pueden cargar, editar y guardar desde la UI contra JSON local.
2. Los documentos de `generate_documents` se pueden revisar y editar desde la UI.
3. La pagina de job permite inspeccionar outputs de cada etapa relevante.
4. `extract_understand` usa LangChain wrappers sin romper fail-closed ni `src/graph.py`.
5. LangSmith permite seguir al menos las etapas LLM relevantes del pipeline actual.
6. `contact_info` se comporta de forma estable y util para review humana.
7. `salary_grade` es estrictamente opcional: si no aparece o es ambiguo, queda en `null` sin romper el nodo.
8. TextSpan/evidence linking se hace por matching determinista.
9. `PlaywrightFetcher` guarda `error_screenshot.png` y usa `bot_profile` persistente.
10. La cascada HTTP -> Playwright -> LLM fallback es visible y auditable.
11. No se agregaron dependencias nuevas de Neo4j para esta fase.
12. `data/jobs/` sigue siendo la unica fuente de verdad operacional.

## Como testear

### Backend

- probar endpoints read/write de editor para `extract_understand` y `match`
- probar endpoints de outputs por stage
- verificar escrituras atomicas sobre `state.json`

### Frontend

- abrir un job real
- cambiar de stage
- inspeccionar artefactos
- editar extraccion
- editar match
- editar documentos
- guardar y recargar para verificar persistencia

### AI

- usar fixtures de postings reales con contacto y sin contacto
- usar fixtures con salary grade y sin salary grade
- verificar que null no rompe el nodo
- verificar que `exact_quote` se mantiene y no aparecen offsets generados por el modelo
- verificar que LangSmith recibe trazas de las etapas instrumentadas

### Scraping

- forzar un fallo JS y verificar `trace/error_screenshot.png`
- verificar uso del `bot_profile`
- verificar fallback HTTP -> Playwright -> LLM
- verificar que artefactos quedan bajo `nodes/scrape/` y `raw/source_text.md`
- verificar que el modo usado y warnings quedan visibles en artifacts y UI

### Comandos de verificacion sugeridos

```bash
python -m pytest tests/interfaces/api -q
python -m pytest tests/nodes/extract_understand -q
python -m pytest tests/core/scraping -q
python -m pytest tests/ -q
```

```bash
cd apps/review-workbench && npm run build
```

## Modificar docs y changelog

Al cerrar cada subfase:

1. actualizar `plan/index_checklist.md`
2. actualizar los planes activos si cambia el alcance real
3. registrar los cambios grandes en `changelog.md`
4. actualizar docs operativas si cambia el flujo del operador o la API

## Templates y referencias a imitar

1. `apps/review-workbench/src/pages/JobStagePage.tsx` como centro de navegacion por job.
2. `apps/review-workbench/src/api/client.ts` como patron de cliente simple hacia FastAPI.
3. `src/interfaces/api/routers/jobs.py` como router principal de surfaces del job.
4. `src/interfaces/api/read_models.py` como capa de lectura/adaptacion de artefactos locales.
5. `src/nodes/extract_understand/prompt/system.md` y `src/nodes/extract_understand/prompt/user_template.md` como disciplina de prompts a preservar.
6. `apps/review-workbench/src/sandbox/pages/NodeEditorSandboxPage.tsx` como base funcional del editor, no como referencia descartable.

## Riesgos y decisiones explicitas

### Riesgo 1

El editor puede quedarse demasiado centrado en JSON crudo.

Decision:

- reusar el `NodeEditor` real en vez de crear otra UI
- cerrar utilidad real sobre JSON local
- luego reducir friccion con affordances guiadas para campos clave

### Riesgo 2

LangChain puede introducir nueva fragilidad si se expande demasiado pronto o sin observabilidad.

Decision:

- limitar la fase actual a `extract_understand`
- conectar LangSmith desde el inicio
- evaluar `match` despues de estabilizar extraccion

### Riesgo 3

El scraping puede crecer demasiado por auto-apply.

Decision:

- priorizar robustez y trazabilidad
- dejar auto-apply fuera del cierre del minimal si amenaza foco o tiempo
- no dejar fuera la visibilidad del modo de scraping y del fallback, porque eso si es parte del minimal

## Strategy de commits

### Commit 1

`feat(ui): complete local job stage review surfaces`

- outputs por stage
- edicion de `extract_understand`
- edicion de `match`
- edicion de documentos

### Commit 2

`feat(ai): harden extract_understand structured extraction`

- fiabilidad de `contact_info`
- `salary_grade` opcional
- LangSmith
- tests reales de extraccion
- span linking determinista

### Commit 3

`feat(scraping): finish minimal fallback and trace evidence`

- screenshot en fallos
- `bot_profile`
- endurecimiento de cascada
- tests y docs operativas

### Commit 4

`docs: close minimal architecture checklist`

- checklist
- changelog
- docs de operador
- notas de verificacion final

## Definicion final de exito

Un operador abre un job en la UI, inspecciona cada etapa relevante, corrige extraccion y matching, edita los documentos generados, guarda todo contra archivos locales reales, y el pipeline sigue orquestado por LangGraph con una capa LLM mas estable y un scraping suficientemente trazable para depuracion.
