# BrowserOS Apply Automation — Design Document

> Estado: exploración activa. Este documento se actualiza a medida que avanza el diseño.

---

## 1. Hallazgos: Cómo hablar con BrowserOS

### El servidor

BrowserOS corre como AppImage (`~/BrowserOS.AppImage`) y expone un servidor HTTP en `http://127.0.0.1:9200`.

### Dos modos de interacción

| Endpoint | LLM | Uso |
|---|---|---|
| `POST /mcp` | **No** | JSON-RPC directo — automatización sin tokens |
| `POST /chat` | Sí | Lenguaje natural → agente con LLM |

**El asistente de BrowserOS dijo que todo pasa por LLM. Es falso.** El `/mcp` endpoint es un servidor MCP estándar que acepta `tools/call` directamente.

### El handshake obligatorio

El `/mcp` requiere el header `Accept: application/json, text/event-stream`. Sin él, devuelve 500 aunque el body sea correcto.

```python
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}
BASE_URL = "http://127.0.0.1:9200/mcp"

def mcp_call(method: str, params: dict, call_id: int = 1) -> dict:
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": call_id}
    r = requests.post(BASE_URL, headers=HEADERS, json=payload)
    return r.json()

# Handshake (sin estado — se puede hacer en cada llamada o una vez por sesión)
mcp_call("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "postulator", "version": "1.0"}
})
```

### Los 60 tools disponibles (sin LLM)

```
# Observación
take_snapshot, take_enhanced_snapshot, get_dom, search_dom,
get_page_content, get_page_links, get_console_logs, take_screenshot

# Navegación
navigate_page, new_page, new_hidden_page, list_pages, get_active_page,
show_page, move_page, close_page

# Interacción
click, click_at, fill, check, uncheck, select_option, upload_file,
press_key, focus, clear, hover, hover_at, type_at, drag, drag_at, scroll
handle_dialog

# Scripting
evaluate_script

# Utilidades
save_pdf, save_screenshot, download_file, browseros_info
```

### El formato snapshot (clave del sistema)

`take_snapshot` devuelve elementos interactivos con IDs numéricos estables **dentro del mismo estado de página**:

```
[124] button "LinkedIn"
[512] link "Apply on company website"    ← así se ve en LinkedIn
[515] button "Save the job"
[464] textbox "Search"
```

Luego se llama `click` con `{"element": 512}` o con el selector CSS. Los IDs se invalidan tras cualquier navegación — siempre hacer nuevo snapshot.

---

## 2. Cómo vamos a llamar al apply

### Arquitectura general

```
BrowserOSClient          PlaybookExecutor         HumanChannel
      │                        │                       │
      │  mcp_call(tools/call)  │                       │
      │◄──────────────────────►│                       │
      │                        │  step fails / unknown │
      │                        │──────────────────────►│
      │                        │  human input          │
      │                        │◄──────────────────────│
```

### El cliente Python base

```python
# src/apply/browseros_client.py
class BrowserOSClient:
    BASE_URL = "http://127.0.0.1:9200/mcp"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    def call(self, tool: str, args: dict) -> dict:
        """Llama un tool directamente sin LLM."""
        ...

    def snapshot(self, page: int) -> list[SnapshotElement]:
        """Retorna elementos interactivos de la página."""
        ...

    def navigate(self, url: str, page: int | None = None) -> int:
        """Navega y retorna el page_id."""
        ...

    def active_page(self) -> PageInfo:
        ...
```

### Un paso del playbook

```python
@dataclass
class Step:
    action: str                    # "click" | "fill" | "upload" | "snapshot" | ...
    selector: str | int | None     # CSS selector o element ID del snapshot
    value: str | None              # para fill/upload
    description: str               # para logs y HITL

    def render(self, context: dict) -> "Step":
        """Sustituye {{variables}} con valores del perfil."""
        ...
```

### Ejecutor con cuerda de Ariadna

```python
class PlaybookExecutor:
    def run(self, playbook: Playbook, context: dict) -> ExecutionResult:
        trace = AriadneTrace()

        for step in playbook.steps:
            result = self._try_step(step, context)

            if result.is_ok:
                trace.record_success(step, result)
            elif result.needs_human:
                human_input = self.human_channel.request(step, result)
                trace.record_human(step, human_input)
                self._apply_human_input(human_input)
            else:
                trace.record_dead_end(step, result)
                return ExecutionResult.failed(trace)

        return ExecutionResult.success(trace)
```

---

## 3. La Cuerda de Ariadna

El laberinto del apply tiene varias bifurcaciones. Cada walkthrough que se completa exitosamente se convierte en un **camino conocido** para futuros applies.

### Estructura del camino

```python
@dataclass
class PathNode:
    step_index: int
    action: str
    url_pattern: str          # regex del URL en ese momento
    snapshot_signature: str   # hash de los elementos visibles clave
    outcome: Outcome          # success | dead_end | human_required

@dataclass
class AriadneTrace:
    job_source: str           # "xing" | "stepstone" | "linkedin"
    path_id: str              # hash reproducible del camino
    nodes: list[PathNode]
    final_status: str         # "submitted" | "dead_end" | "human_required"
    dead_end_reason: str | None
```

### Los tipos de bifurcación conocidos

```
URL del job
    │
    ├─ 404 / 410 ──────────────────────────► dead_end: "job_expired"
    │
    ├─ Redirect a sitio externo de empresa ─► dead_end: "external_ats"
    │   (Greenhouse, Lever, Workday, etc.)       (candidato para nuevo playbook)
    │
    ├─ "Easy Apply" en el portal ──────────► camino feliz → ejecutar playbook
    │
    ├─ Login requerido ─────────────────────► human_required: "login_needed"
    │
    ├─ CAPTCHA / antibot ───────────────────► human_required: "captcha"
    │
    ├─ Formulario con campos desconocidos ──► human_required: "unknown_form"
    │
    └─ Modal de confirmación inesperado ────► human_required: "unexpected_modal"
```

### El playbook como grafo de caminos

Un playbook no es una lista lineal sino un árbol con ramas conocidas:

```json
{
  "source": "xing",
  "version": "2026-04-01",
  "known_paths": {
    "easy_apply_modal": {
      "trigger": {"element_text": "Jetzt bewerben", "url_contains": "xing.com"},
      "steps": [...]
    },
    "external_ats_greenhouse": {
      "trigger": {"url_contains": "greenhouse.io"},
      "steps": [...]
    }
  },
  "dead_ends": {
    "job_expired": {"url_patterns": ["404", "job-not-found"]},
    "antibot": {"snapshot_contains": ["verify you are human", "captcha"]}
  }
}
```

### Aprendizaje del laberinto

Cuando se descubre un camino nuevo (con o sin ayuda humana), la traza se guarda y puede revisarse para crear un nuevo playbook branch:

```
data/apply_knowledge/
  xing/
    paths/
      easy_apply_modal_v1.json     ← camino conocido
      easy_apply_modal_v2.json     ← variante descubierta después
    dead_ends/
      job_expired_patterns.json
    unknowns/
      2026-04-01_job_12345.json    ← walkthrough humano pendiente de clasificar
```

---

## 4. Cuándo y cómo avisar al humano

### Niveles de interrupción

```python
class InterruptionLevel(Enum):
    SILENT    = "silent"    # log, continúa solo
    NOTIFY    = "notify"    # avisa pero no bloquea
    PAUSE     = "pause"     # espera respuesta antes de continuar
    ABORT     = "abort"     # para y documenta el dead end
```

| Situación | Nivel |
|---|---|
| Campo pre-llenado con valor incorrecto | PAUSE |
| Login requerido | PAUSE |
| CAPTCHA | PAUSE |
| Formulario con campos desconocidos | PAUSE |
| Modal inesperado | PAUSE |
| Antibot detectado (timeout / bloqueo) | NOTIFY + ABORT |
| Redirect a ATS externo no soportado | NOTIFY + ABORT |
| 404 / job expirado | SILENT + ABORT |
| Apply enviado con éxito | NOTIFY |

### El canal humano

El MVP usa terminal (stdin/stdout). En el futuro puede ser Textual TUI, notificación de sistema, o webhook.

```python
class HumanChannel:
    def request(self, step: Step, context: FailContext) -> HumanInput:
        """Bloquea hasta recibir respuesta del usuario."""
        ...

class TerminalHumanChannel(HumanChannel):
    def request(self, step: Step, context: FailContext) -> HumanInput:
        print(f"\n[POSTULATOR] Necesito ayuda en: {step.description}")
        print(f"  URL actual: {context.url}")
        print(f"  Problema: {context.reason}")
        print(f"  Screenshot: {context.screenshot_path}")
        print("  Opciones: [s]kip / [r]etry / [m]anual (toma control) / [a]bortar")
        choice = input("> ").strip()
        return HumanInput.parse(choice)
```

### Screenshot automático en cada pausa

Antes de interrumpir al humano, siempre guardar screenshot:

```python
async def _before_pause(self, job_id: str) -> Path:
    result = self.client.call("take_screenshot", {"page": self.active_page_id})
    path = APPLY_DIR / job_id / "screenshots" / f"{timestamp()}.png"
    path.write_bytes(base64.b64decode(result["data"]))
    return path
```

---

## 5. Grabar la interacción del usuario (Recording)

BrowserOS no tiene un "modo grabación" nativo. Pero se puede reconstruir desde CDP.

### Estrategia via CDP (Chrome DevTools Protocol)

BrowserOS expone CDP en `http://127.0.0.1:9101`. Desde ahí se puede:
- Escuchar eventos DOM (clicks, inputs, navigations)
- Reconstruir la secuencia de acciones del usuario

```python
# Pseudocódigo del recorder
class CDPRecorder:
    CDP_URL = "ws://127.0.0.1:9101/devtools/page/{target_id}"

    async def record_session(self, target_id: str) -> list[RecordedAction]:
        async with websocket.connect(self.CDP_URL.format(target_id=target_id)) as ws:
            await ws.send(json.dumps({"method": "Page.enable", "id": 1}))
            await ws.send(json.dumps({"method": "Runtime.enable", "id": 2}))
            # Inject listener for user events
            await ws.send(json.dumps({
                "method": "Runtime.evaluate",
                "params": {"expression": RECORD_SCRIPT},
                "id": 3
            }))
            return await self._collect_events(ws)
```

### Estrategia alternativa: snapshot diff

Más simple. Tomar snapshots periódicos durante la sesión manual y comparar diffs para inferir qué hizo el usuario:

```
snapshot_t0: [412] button "Jetzt bewerben"
snapshot_t1: [modal abierto] [501] textbox "Name"   ← el usuario hizo click en 412
snapshot_t2: [501] textbox "Name" value="Juan Pablo" ← el usuario llenó el campo
```

El diff entre snapshots se convierte directamente en pasos del playbook.

### Flujo completo de grabación manual

```
1. Postulator detecta camino desconocido (nuevo portal, nuevo formulario)
2. Avisa al usuario: "Necesito que hagas el apply manualmente esta vez"
3. BrowserOS abre la página en primer plano
4. El recorder escucha eventos CDP o toma snapshots cada N segundos
5. Usuario completa el apply
6. Recorder genera borrador de playbook
7. Postulator pregunta: "¿Guardo este camino para futuros applies?"
8. Si sí → se agrega a apply_knowledge/
```

---

## 6. Walkthrough en vivo — LinkedIn Easy Apply (2026-04-01)

### Lo que pasó

Primer dry-run completo via MCP directo, sin LLM, recorriendo el flujo completo de LinkedIn Easy Apply hasta la pantalla de review. Se paró antes de `Enviar solicitud`.

**Job:** Data Scientist | Remote — Crossing Hurdles
**Trace:** `future_docs/applying/traces/linkedin_easy_apply/`

### Pasos reales observados

| Paso | Nombre | Campos clave | Human required? |
|---|---|---|---|
| 1 | Contact info | First name, Last name, Phone, Email — todos pre-llenados desde perfil LinkedIn | No |
| 2 | CV selection | Muestra CVs previamente subidos con radio buttons. `CV_english.pdf` ya estaba | No |
| 3 | Experience review | Entradas de experiencia pre-llenadas. Solo botones Edit/Remove | No |
| 4 | Additional questions | En este job: sin preguntas extras. Solo "Revisar tu solicitud" | No (this time) |
| 5 | Review | Resumen completo + `Enviar solicitud` | **Sí — confirm antes de submit** |

### Bifurcación descubierta: "¿Descartar solicitud?"

Al cerrar el modal con el botón `[2347] Descartar`, apareció un modal de confirmación con:
- `[7851/7860] button "Descartar"` — confirmar descarte
- `[7862] button "Guardar"` — guardar borrador

**Esto es una bifurcación nueva en el árbol.** Hay que manejarla en el executor.

### Formato snapshot clave

Los IDs de snapshot **no son estables entre sesiones** — solo dentro de la misma carga de página. Lo que sí es estable es el **texto del elemento**. El executor debe buscar por texto, no por ID numérico.

```python
# MAL — IDs cambian entre sesiones
click(element=3444)

# BIEN — texto es estable
click(element_text="Ir al siguiente paso")
click(element_text="Enviar solicitud")
```

### Coste real del walkthrough

- Tokens LLM gastados: **0**
- Llamadas MCP: ~15 calls
- Tiempo: ~20 segundos (incluye sleeps de espera de carga)

---

## 7. Lo que falta explorar

- [x] **Verificar si el MCP server es stateless o stateful** — Es stateless entre requests HTTP, pero el browser sí mantiene estado (cookies, DOM). Los IDs de snapshot cambian entre cargas pero el texto del elemento es estable. → **Usar text-based selectors, no IDs numéricos.**
- [ ] **Verificar si el MCP server es stateless o stateful** (extended) entre llamadas. Los IDs de snapshot parecen sobrevivir entre llamadas en la misma sesión de navegador — confirmar.
- [ ] **CDP recorder** — conectar websocket a `9101` y verificar qué eventos llegan con `Page.enable` + `Input.enable`.
- [ ] **Detección de antibot** — Cloudflare/Datadome aparecen en el snapshot como elementos específicos. Documentar los patrones.
- [ ] **ATS externos** — Greenhouse, Lever, Workday, SAP SuccessFactors tienen formularios distintos. Cada uno necesita su propio playbook branch.
- [ ] **Manejo de uploads multi-paso** — algunos portales abren un segundo diálogo del OS para seleccionar archivo. `upload_file` de BrowserOS debería manejarlo, verificar.
- [ ] **Estado del servidor BrowserOS entre reinicios** — las cookies de login sobreviven en `~/.config/browser-os/Default/`? ¿O hay que re-autenticar?
- [ ] **Throttling** — cuántas calls por segundo aguanta el MCP sin que el browser se queje.

---

## 7. Próximos pasos propuestos

1. **`BrowserOSClient`** — clase Python que wrappea el MCP, con `initialize()`, `call()`, `snapshot()`, `navigate()`.
2. **`PlaybookExecutor`** — ejecuta un playbook JSON con variables, maneja errores básicos.
3. **Playbook de XING Easy Apply** — construido manualmente primero, luego automatizado con el recorder.
4. **`AriadneTrace`** — graba la ejecución y detecta bifurcaciones.
5. **`TerminalHumanChannel`** — MVP del canal de interrupción.
6. **CDP Recorder** — prototipo que convierte una sesión manual en un borrador de playbook.
