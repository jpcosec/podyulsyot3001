# Ariadne Recording Pipeline

Date: 2026-04-05
Status: design-only

## Purpose

Define how raw motor sessions become normalized Ariadne paths. The recording
pipeline is Ariadne's intake system. It runs when the BrowserOS Agent motor or
Human motor is active, watches what happens, and produces draft paths.

## Pipeline stages

```
watch → record → process → update
```

### 1. Watch — capture raw events from the session

The recording pipeline attaches to a motor session and captures raw events.
Different motors produce different raw data.

**BrowserOS Agent motor (MCP proxy):**

The MCP proxy sits between the OpenBrowser agent and BrowserOS port 9200.
Every `tools/call` request and response is intercepted and logged.

| Captured data | Source |
|---|---|
| Tool call name + arguments | MCP proxy request |
| Tool call result | MCP proxy response |
| Timestamp | Proxy clock |
| Snapshot elements (periodic) | `take_snapshot` calls (interleaved or piggy-backed) |
| Screenshots | `save_screenshot` calls or periodic captures |
| Agent prompts/responses | Agent session log (if accessible) |
| HITL interactions | `HumanInteractTool` callback events |

**Human motor (CDP + MCP):**

The recording pipeline connects to BrowserOS CDP (port 9101) and optionally
takes periodic MCP snapshots (port 9200).

| Captured data | Source |
|---|---|
| Click events (tag, text, x, y, name) | CDP `Runtime.consoleAPICalled` via injected capture script |
| Change events (name, value, type) | Same capture script |
| Submit events (action, method) | Same capture script |
| Navigation events | CDP `Page.frameNavigated` |
| Form submissions (POST) | CDP `Network.requestWillBeSent` |
| Snapshot elements (periodic) | MCP `take_snapshot` calls |
| Screenshots | MCP `save_screenshot` calls |
| Human annotations | Annotation interface (terminal, TUI, or key bindings) |

**Capture script re-injection:** on every `Page.frameNavigated` event, the
in-page capture script must be re-injected via `Runtime.evaluate` because
navigation destroys the previous page context.

### 2. Record — log raw events as a structured timeline

Raw events from any source are normalized into a flat timeline:

```python
@dataclass
class RawRecordingEvent:
    timestamp: str              # ISO timestamp
    source: str                 # "mcp_proxy" | "cdp" | "human_annotation"
    event_type: str             # "tool_call" | "click" | "change" | "navigate" | "snapshot" | "annotation"
    data: dict                  # event-specific payload
```

The timeline is append-only during the session. No correlation or normalization
happens yet — just ordered capture.

### 3. Process — correlate and normalize into common language

This is the core transformation: raw timeline → `AriadneStep` list.

**Step boundary detection:**

Events are grouped into steps. Boundaries are detected by:
- Navigation events (URL change = new step)
- Snapshot-to-snapshot intervals (observe → actions → observe = one step)
- Time gaps above a threshold (configurable, e.g., 3 seconds)
- Explicit human annotations marking step boundaries

**Element identity stabilization:**

Raw events reference elements in backend-specific ways:
- MCP tool calls use numeric element IDs (session-scoped, unstable)
- CDP events use tag + text + coordinates

Stabilization correlates these with the nearest snapshot to produce text-based
identification for `AriadneTarget.text` fields. If the element has a stable CSS
selector (from CDP capture or MCP `search_dom`), it also populates `AriadneTarget.css`.

**Normalization rules:**

| Raw event | AriadneAction intent | AriadneTarget source |
|---|---|---|
| MCP `click(element: 512)` | `click` | `text:` from snapshot element 512 |
| MCP `fill(element: 340, value: "Juan")` | `fill` | `text:` from snapshot element 340 |
| MCP `select_option(element: 401, value: "DE")` | `select` | `text:` from snapshot element 401 |
| MCP `upload_file(element: 205, filePath: "...")` | `upload` | `text:` from snapshot element 205 |
| MCP `evaluate_script` (React setter pattern) | `fill_react_controlled` | `css:` extracted from script |
| CDP `click {tag, text, x, y}` | `click` | `text:` from event, `region:` from coordinates |
| CDP `change {name, value}` | `fill` | `text:` from nearest snapshot match or `css:` from name |
| CDP `submit {action}` | `click` | inferred from last click target |

**Profile value substitution:**

Known candidate values are replaced with `{{placeholder}}` templates:
- Values matching profile fields → `{{profile.first_name}}`, `{{profile.email}}`, etc.
- Values matching job fields → `{{job.job_title}}`, `{{job.company_name}}`, etc.
- File paths → `{{cv_path}}`, `{{cv_filename}}`
- Unknown values left as literals, flagged for human review

**Observe block generation:**

For each step, the snapshot taken before the step's actions defines the
`AriadneObserve.expected_elements` list. Elements that were interacted with
in the step are marked as required; others present in the snapshot may be
included as optional context.

**Bifurcation and dead-end detection:**

- If the agent or human encountered a choice point (multiple valid next actions),
  record as a bifurcation on the step's `ariadne_tag`
- If the flow hit a wall (external ATS redirect, expired job, CAPTCHA without
  resolution), record as a dead end
- Agent motor: detected from agent prompts that mention alternatives or failures
- Human motor: detected from explicit human annotations

### 4. Update — store the normalized path in Ariadne

The processed output is an `AriadnePath` with status `draft`. It's handed to
Ariadne storage via `recorder.py` → `storage.py`.

What gets stored:
- The normalized `AriadnePath` as JSON
- Raw recording timeline (for debugging and re-processing)
- Screenshots captured during recording (evidence)
- Recording session metadata (who, when, which motor, which portal)

The draft path is now available for:
- Human review (inspect the normalized steps, correct errors)
- Verification replay (a deterministic motor replays it to confirm it works)
- Promotion (see `promotion.md`)

## Recording session lifecycle

```
1. Operator starts a recording session
   → CLI command or TUI action
   → specifies: portal, motor (agent or human), profile data

2. System prepares capture infrastructure
   → MCP proxy starts (for agent motor)
   → CDP WebSocket connects (for human motor)
   → Snapshot schedule begins
   → Browser opens to portal entry point

3. Motor acts (agent navigates autonomously, or human navigates manually)
   → recording pipeline watches and captures raw events

4. Session ends
   → operator signals stop, or agent completes, or flow reaches end
   → capture infrastructure tears down

5. Processing runs
   → raw timeline → correlated steps → normalized AriadnePath
   → profile values substituted with templates
   → bifurcations and dead ends annotated

6. Draft path stored
   → AriadnePath written to Ariadne storage with status "draft"
   → raw timeline and screenshots archived alongside
```

## What the recording pipeline is NOT

- Not a motor — it never acts on pages
- Not Ariadne storage — it produces artifacts for storage, but storage owns the schema
- Not a translator — translators compile common language out to motor format;
  the recording pipeline normalizes motor format in to common language (inverse direction)

## Implementation dependencies

- Ariadne common-language models (defines the output format)
- Ariadne storage (receives and persists draft paths)
- MCP proxy (for BrowserOS-based capture)
- CDP WebSocket client (for human session capture)
- Snapshot + screenshot capture utilities
- Profile value detection (for template substitution)

## Open questions

1. Should the recording pipeline run as a real-time stream processor (normalize
   as events arrive) or as a batch processor (collect all events, normalize after
   session ends)? Real-time enables live preview; batch is simpler.
2. How do we handle recording failures? If the capture script isn't injected
   properly, or the MCP proxy misses events, is the partial recording usable?
3. Should the raw timeline be stored in a structured format (JSON lines, SQLite)
   or as a plain log? Structured enables re-processing; plain is simpler.
4. How granular should step boundary detection be? Too fine → too many steps;
   too coarse → steps contain unrelated actions. Is human override sufficient
   for edge cases?
5. Should the recording pipeline detect when the observed flow matches an
   existing Ariadne path and produce a diff instead of a new path? This would
   enable path update without full re-recording.
