# Ariadne 2.0 — Ontología base (draft superficial)

Documento de trabajo. Captura las decisiones de modelado conversadas antes de
aterrizar tipos concretos o cableado de LangGraph. Sirve como piso firme para
que cualquier diseño posterior (actores, nodos, persistencia) sea coherente.

---

## 1. Principio rector

Ariadne opera sobre **dos niveles de abstracción simultáneos**:

- **El DOM en grande** — estructura semántica del portal, no HTML byte a byte.
- **El grafo topológico** — habitaciones y transiciones entre habitaciones.

Ninguna pieza del sistema toca HTML crudo excepto el traductor del Labyrinth
y el adaptador de navegador. Todo lo demás habla en vocabulario abstracto.

## 1.1 Infraestructura de browser: BrowserOS

BrowserOS es el **único runtime de Chromium** del sistema. No es una alternativa
al adaptador — es la capa física que todos comparten:

- **Crawl4AI** se conecta al Chromium de BrowserOS para ejecutar scripts y
  acciones del fast path (incluidos los C4AScripts del Nivel 0).
- **Delphi (LLM)** se conecta a BrowserOS vía MCP para razonamiento visual
  en cold path.
- **BrowserOS agent** (nativo) puede navegar de forma autónoma — sus sesiones
  pueden grabarse con el Chromium Recorder para captura pasiva de threads.

**Paso 0 de cualquier run**: verificar que BrowserOS esté encendido. Si no,
levantarlo. Esta lógica vive en `BrowserOSAdapter.__aenter__` / `is_healthy()`.
El código ya está implementado (`plan_docs/design/browseros-adapter-lifecycle.md`).
El CLI solo hace `async with adapter:` y nunca posee lógica de arranque.

---

## 2. Las tres entidades núcleo

### 2.1 `Labyrinth` — atlas de habitaciones

Grafo **sin aristas**. Es un catálogo de todas las habitaciones conocidas del
portal.

- **Nodos**: pares `(URLNode, RoomState) → Skeleton`
- **Rol**: responder *"¿en qué habitación estoy?"* y *"¿qué elementos hay aquí?"*
- **No guarda**: rutas, historia de misiones, confianza
- **Sí guarda**: habitaciones rotas, 404s, modales aleatorios, overlays — todo
  es información útil para el LLM en cold path

El Labyrinth es exhaustivo y sin juicio. Un camino roto es información, no
basura.

### 2.2 `AriadneThread` — grafo de transiciones

Grafo **con aristas** sobre los nodos del Labyrinth. Memoria procedural de
misiones exitosas.

- **Nodos**: referencias a habitaciones del Labyrinth (`room_id`)
- **Aristas**: `(room_from, [actions...], room_to)` — secuencias que
  históricamente cruzaron de una habitación a otra
- **Por misión**: un mismo Labyrinth tiene varios Threads (uno por misión)
- **Nace**: solo cuando una misión completa se cierra con éxito
- **No sabe semántica**: solo recuerda *qué se hizo antes*, no *por qué
  funcionó*. La interpretación la hace Teseo mirando el Labyrinth o el LLM.

### 2.3 `Action` — interacción con el DOM

Cualquier operación sobre un elemento del DOM abstracto. Tres variantes:

| Tipo | Efecto sobre el esqueleto | Ejemplos |
|---|---|---|
| `PassiveAction` | Ninguno | `hover`, `focus`, `scroll` |
| `ExtractionAction` | Ninguno (solo lee) | `extract_list`, `read_field`, `harvest_cards` |
| `TransitionAction` | **Muta el esqueleto** | `click(boton)`, `submit_form`, `accept_modal` |

Solo las `TransitionAction` generan aristas en el Thread y habitaciones
potencialmente nuevas en el Labyrinth.

---

## 3. Anatomía de una habitación

Una habitación es un par `(URLNode, RoomState)` que apunta a un `Skeleton`.

### 3.1 `URLNode`

Identidad gruesa por patrón de URL.

- `id` semántico (`home`, `search_index`, `job_detail`)
- `url_template` con slots nombrados y query params opcionales
  - Ej: `https://www.stepstone.de/jobs/in-{city}{?page,sort}`
- `match(raw_url) -> bool` y `extract_params(raw_url) -> dict`

### 3.2 `RoomState`

Variante visual dentro de una misma URL.

- `id` (ej. `home.anon_with_cookie_modal`)
- `parent_url_node`
- **Predicado de presencia** sobre el esqueleto
- Metadata: `is_modal_overlay`, `blocks_interaction`, `is_terminal`, etc.

Un `(home)` puede tener N `RoomState`s: `home.anon`, `home.logged_in`,
`home.with_ad_modal`, `home.with_cookie_modal`, etc. Los "handlers" de
interrupciones no son una clase aparte — son simplemente `RoomState`s con
metadata `is_modal_overlay=True`.

### 3.3 `Skeleton` — la abstracción del HTML

Árbol de `AbstractElement`s tipados. Invariante al contenido, sensible a la
estructura.

- **Tipos de elemento**: `navbar`, `modal`, `formulario`, `campo_texto`,
  `boton`, `lista`, `card`, `div_texto`, `link`, `imagen`, `dropdown`, ...
- Cada elemento conserva: tipo, rol, selector estable, y **slots** de contenido
- **Slots** son los huecos variables (texto de un título, items de una lista)
  que cambian entre visitas sin alterar la topología

Tres capas dentro de cada habitación:

1. **`Skeleton`** — invariante, guardado en el Labyrinth
2. **`ContentSlots`** — metadata de qué huecos hay y de qué tipo
3. **`DomInstance`** — el esqueleto rellenado con valores del turno, efímero

---

## 4. El juez único: el esqueleto

La frontera entre `Action` y `TransitionAction` la decide el esqueleto:

> Una acción es transición si, comparando los esqueletos abstractos antes y
> después, hay al menos un `AbstractElement` nuevo, removido, o cambiado de
> tipo. Los cambios de contenido dentro de slots no cuentan.

Consecuencias:

- Llenar un input no es transición (solo cambia un slot).
- Abrir un dropdown sí es transición (aparecen elementos nuevos).
- Una publicidad que se autoinyecta 300ms después de cargar es una transición
  involuntaria — crea una habitación nueva y fuerza cold path.
- Cambiar el orden de una lista (sort-by) no es transición — el esqueleto es
  idéntico, solo cambian los slots. El orden se resuelve como parámetro de la
  `ExtractionAction` o en postprocesamiento.

---

## 5. Granularidad y colapso diferido

**Regla operativa**: preferimos granularidad fina que gruesa, y *colapsamos
después*. Si el sistema detecta muchos esqueletos que difieren solo en algo
menor (ej. estado de un acordeón), ese diff puede promoverse a un
`AbstractElement` nuevo de tipo `control`, y las N habitaciones anteriores
colapsan en una sola con un slot de control. La refactorización es barata
porque no hay aristas que reescribir en bloque — el Thread solo referencia
`room_id`s y el Labyrinth los puede remapear.

Esto evita el dilema de modelar-perfecto-desde-el-día-uno.

---

## 6. El bucle cognitivo (Sense-Think-Act)

```
  observe  (Sensor.perceive → raw_html, raw_url, screenshot)
     │
     ▼
  Labyrinth.identify(snapshot)
     │
     ├── (url, state) CONOCIDO ──► FAST PATH
     │                              │
     │                              ▼
     │                         Thread.next_step(room_id)
     │                              │
     │                              ├── hay paso ─► ejecuta actions
     │                              └── no hay    ─► COLD PATH
     │
     └── (url, state) DESCONOCIDO ──► COLD PATH
                                       │
                                       ▼
                      LLM recibe: raw_html + screenshot + Labyrinth context
                      LLM devuelve:
                        a) skeleton nuevo  → Labyrinth.expand()
                        b) room_id sugerido
                        c) acción a ejecutar
                                       │
                                       ▼
                                  ejecuta acción
                                       │
                                       ▼
                         ¿misión cumplida? ── sí ─► sella Thread y EXIT
                                            └─ no ─► loop a observe
```

### Notas sobre el cold path

- El LLM hace **dos trabajos distintos**: extraer esqueleto (trabajo del
  Labyrinth) y proponer acción (trabajo de Delphi). Conviene separarlos en
  llamadas distintas para no desperdiciar el esqueleto si la acción falla.
- El contexto que se le pasa al LLM **incluye las anti-rutas conocidas** del
  Labyrinth: *"estas opciones existen, estas ya sabemos que llevan a 404".*
- `Thread`s previos de otras misiones del mismo portal sirven como ejemplos de
  acciones que funcionaron ahí antes.

---

## 7. Modos de ejecución (jerarquía de velocidad)

Un mismo `AriadneThread` puede ejecutarse en tres modos según el nivel de
confianza y disponibilidad de artefactos compilados:

### Nivel 0 — C4A Script (compilado)

Un Thread completamente resuelto y verificado puede **compilarse** a un
`C4AScript` usando el modo ultra-rápido de Crawl4AI (`c4ascripts`).

- No hay LangGraph en runtime. No hay Python overhead. Es ejecución directa
  de un script nativo de Crawl4AI.
- El script se genera a partir del Thread — no se escribe a mano.
- Es el artefacto de producción de un Thread maduro: Thread → compilar →
  C4AScript → deploy.
- Si el script falla (portal cambió, nuevo modal), se degrada al Nivel 1.
- Referencia: `docs/reference/external_libs/crawl4ai/c4a_script_reference`

### Nivel 1 — Theseus (fast path, $0)

Thread activo interpretado en runtime vía LangGraph. Labyrinth identifica la
habitación, Thread entrega el paso, Motor ejecuta. Descrito en sección 6.

### Nivel 2 — Delphi (cold path, LLM)

Rescate cuando Theseus no puede identificar la habitación o el Thread no tiene
paso. Descrito en sección 6.

### Nivel 3 — HITL

Breakpoint humano cuando el circuit breaker de Delphi se agota.

---

## 8. Modos de recording

Dos fuentes de verdad para construir y expandir Threads:

### Recording activo (LLM-driven)

Se construye durante las corridas de Delphi (Nivel 2). Cada decisión exitosa
del LLM emite un `TraceEvent` al Recorder, que asimila la nueva
`(room, action, room_next)` en el Thread. Este es el camino principal de
aprendizaje del sistema.

### Recording pasivo (Chromium/Puppeteer)

El usuario navega manualmente en Chrome → exporta la sesión como JSON de
Chrome DevTools Recorder → el Recorder lo ingiere vía
`Recorder.ingest_passive_trace(devtools_json)`. Produce un "thread de bajo
nivel" escrito en formato Puppeteer que luego puede promoverse a Thread de
Ariadne.

**Estado: diseñado, no en scope para la implementación actual.** Se deja
documentado para no perder el modelo mental, pero no se implementa en esta
fase.

---

## 9. Lo que **no** está definido todavía

Este spec deliberadamente no cubre:

- Representación concreta del `Skeleton` (árbol vs grafo, formato serializado).
- Cómo se entrena o construye el traductor `raw_html → Skeleton` (heurístico,
  LLM, mixto).
- Estructura interna de una `Transition` sellada en el Thread (metadata,
  timestamps, confianza, variantes).
- Cableado a LangGraph (nodos, aristas, forma del `AriadneState`).
- Persistencia del Labyrinth y los Threads entre ejecuciones.
- Handlers reusables de modales como promoción automática desde el Labyrinth.
- Compilador Thread → C4AScript (formato de salida, condiciones de promoción,
  estrategia de degradación al fallar).

Cada uno de esos merece su propio documento una vez que la ontología de este
archivo esté sellada.

---

## 8. Glosario rápido

| Término | Qué es |
|---|---|
| `Labyrinth` | Atlas de habitaciones conocidas del portal. Sin aristas. |
| `AriadneThread` | Grafo de transiciones exitosas para una misión. |
| `URLNode` | Patrón de URL que define una "página". |
| `RoomState` | Variante visual de una URL (modal, logged-in, etc). |
| `Skeleton` | Árbol abstracto de elementos tipados. Invariante al contenido. |
| `AbstractElement` | Nodo tipado del skeleton (`boton`, `formulario`, etc). |
| `Slot` | Hueco de contenido variable dentro de un elemento. |
| `DomInstance` | Skeleton rellenado con valores del turno. Efímero. |
| `Action` | Interacción con el DOM. Pasiva, extractiva o de transición. |
| `TransitionAction` | Acción que muta el skeleton. Única que genera aristas. |
| `Teseo` | Ejecutor determinista del fast path. |
| `Delphi` | Rescate LLM/HITL en cold path. |
| `Recorder` | Asimilador que expande Labyrinth y teje Threads. |
