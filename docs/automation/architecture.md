# Automation Architecture

Navigation guide to the automation system's current boundaries and implementation homes.

## Core design principle

Portal knowledge and browser execution are separate concerns:

- `Labyrinth` owns all knowledge about a portal: URL patterns, room states, DOM skeletons, and available actions.
- `AriadneThread` owns the transition graph for a specific mission over a Labyrinth.
- `BrowserAdapter` owns physical I/O (perceive + act) without knowing about missions or portal structure.

That separation means a Thread can be replayed through a different adapter without touching the portal model.

## Browser infrastructure: BrowserOS

BrowserOS is the **single browser runtime** for the entire system. It is not an alternative to Crawl4AI — it is the Chromium instance that everything connects to.

### Port map

| Port | Protocol | Used by |
|------|----------|---------|
| 9000 | CDP (WebSocket) | Crawl4AI → `BrowserConfig(cdp_url="ws://localhost:9000")` |
| 9100 | HTTP/SSE MCP | Delphi LLM cold path |
| 9200 | Agent API | BrowserOS native agent (autonomous navigation, passive recording) |
| 9300 | Extension | Chromium extension internal |

- **Crawl4AI** connects to port 9000 (CDP). Does **not** launch its own browser.
- **Delphi (LLM)** connects to port 9100 (MCP) for visual rescue and reasoning.
- **BrowserOS agent** (port 9200) can navigate autonomously — its sessions can be recorded for passive thread capture.

**Step 0 of every run**: verify BrowserOS is up (`GET http://localhost:9100/health`). If not, start it. This lifecycle logic lives inside the `BrowserOSAdapter` (`__aenter__` / `is_healthy()`). See `plan_docs/design/browseros-adapter-lifecycle.md`. The CLI only calls `async with adapter:` and never owns startup logic.

## Ontology (three entities)

### `Labyrinth` — atlas of rooms

A graph of `(URLNode, RoomState) → Skeleton` pairs. No edges — it does not know about routes.

- **`URLNode`**: URL pattern with named slots. Answers "which page am I on?"
- **`RoomState`**: visual variant of a URL (modal overlays, logged-in/out, etc). Answers "which variant am I seeing?"
- **`Skeleton`**: abstract tree of typed `AbstractElement`s (navbar, formulario, boton, lista, card…). Invariant to slot content (text, values). The judge for what counts as a transition.

Labyrinth is exhaustive and non-judgmental. Broken states, 404s, ad overlays are stored as rooms — all are context for Delphi.

### `AriadneThread` — transition graph

A directed graph of `room_id` nodes with edges `(room_from, [actions…], room_to)`. One Thread per mission per portal. Only created after a full successful run. Does not know action semantics — Theseus reads the Labyrinth to interpret them.

### `Action` — DOM interaction

Any interaction with a DOM element. Three variants:

| Type | DOM effect | Examples |
|---|---|---|
| `PassiveAction` | None | hover, scroll |
| `ExtractionAction` | None (read only) | extract_list, harvest_cards, read_field |
| `TransitionAction` | Mutates the Skeleton | click(button), submit_form, accept_modal |

Only `TransitionAction`s generate edges in the Thread and potentially new rooms in the Labyrinth.

**Transition judge**: an action is a transition if `skeleton(after) ≠ skeleton(before)` at the structural level — typed elements added, removed, or reclassified. Changes to slot content (text, input value) do not count.

## Execution modes (speed hierarchy)

A proven `AriadneThread` can execute at three levels depending on maturity:

| Level | Mode | Cost | Mechanism |
|---|---|---|---|
| **0** | C4A Script | Near-zero | Thread compiled to a native Crawl4AI `c4ascript`. No LangGraph, no Python overhead. Degrades to Level 1 on failure. |
| **1** | Theseus (fast path) | $0 | Thread interpreted at runtime via LangGraph. |
| **2** | Delphi (cold path) | LLM tokens | LLM rescue when Theseus can't identify room or Thread has no step. |
| **3** | HITL | Human time | Terminal breakpoint when Delphi's circuit breaker is exhausted. |

The C4A Script is the production artifact of a mature Thread. Generation: `Thread → compile → C4AScript`. See `docs/reference/external_libs/crawl4ai/c4a_script_reference`.

## Runtime flow (Levels 1–3)

```
Interpreter → Observe → Theseus ──(fast path)──► Execute → Recorder → Observe (loop)
                                └──(cold path)──► Delphi  → Execute → Recorder → Observe (loop)
                                                      └──(circuit breaker)──► HITL
```

1. **Interpreter**: resolves raw instruction to `mission_id`. Loads the AriadneThread if one exists.
2. **Observe**: `Sensor.perceive()` — one DOM read per turn. Snapshot is shared by Theseus and Delphi without double I/O.
3. **Theseus** (fast path, $0): `Labyrinth.identify(snapshot)` → `room_id`. `Thread.next_step(room_id)` → action sequence. If no match → cold path.
4. **Execute**: `Motor.act(action)`. Single write point to the browser. Emits a `TraceEvent` appended to state.
5. **Delphi** (cold path): receives raw HTML + screenshot + Labyrinth context (including known dead-ends). Extracts new Skeleton, proposes action. Increments circuit breaker.
6. **Recorder**: reads `trace`, calls `Labyrinth.expand()` and `Thread.add_step()` as appropriate. Silent node — does not decide flow.
7. **HITL**: activates when Delphi's circuit breaker limit is reached (Law 4).

## Physical laws (non-negotiable)

1. **Event loop is sacred**: zero blocking I/O in the LangGraph hot loop.
2. **Browser is a singleton**: one browser context per mission.
3. **DOM is hostile**: code injection (Set-of-Mark) operates on disconnected overlays. Never mutate the live tree.
4. **Routing is finite**: circuit breakers required. Every Delphi rescue loop has a hard limit before escalating to HITL.

## Source layout

```
src/automation/
│
├── contracts/                  # Layer 0 — no dependencies on anything internal
│   ├── sensor.py               # Sensor protocol + SnapshotResult
│   ├── motor.py                # Motor protocol + MotorCommand + ExecutionResult
│   └── state.py                # AriadneState (LangGraph state dict)
│
├── adapters/                   # Layer 1 — physical implementations
│   └── browser_os.py           # BrowserOSAdapter (implements Sensor + Motor via Crawl4AI)
│
├── ariadne/                    # Layer 2 — domain
│   ├── labyrinth/              # Portal atlas
│   │   ├── url_node.py         # URLNode — URL pattern with named slots
│   │   ├── room_state.py       # RoomState — visual variant of a URL
│   │   ├── skeleton.py         # Skeleton + AbstractElement
│   │   └── labyrinth.py        # Labyrinth — the full atlas graph
│   ├── thread/                 # Mission transition graph
│   │   ├── action.py           # PassiveAction, ExtractionAction, TransitionAction
│   │   └── thread.py           # AriadneThread
│   └── extraction/             # PortalDictionary
│       ├── portal_dictionary.py # AbstractElement → stable CSS selector mapping
│       └── schema_builder.py   # generate_schema() wrapper (one LLM call → cached forever)
│
└── langgraph/                      # Layer 3 — LangGraph wiring
    ├── nodes/
    │   ├── interpreter.py      # Instruction → mission_id
    │   ├── observe.py          # Sensor.perceive() — one read per turn, shared by all actors
    │   ├── theseus.py          # Deterministic fast-path actor
    │   ├── delphi.py           # LLM cold-path rescue
    │   └── recorder.py         # Trace assimilation into Labyrinth + Thread
    └── builder.py              # Assembles the LangGraph
```

**Dependency rule** — a layer may only import from layers above it (lower number), never below:

```
contracts  ←  adapters  ←  ariadne  ←  graph
```

`contracts` is the only module imported by everyone and imports nothing internal. Design and seal it first.

## Component map

| Component | Responsibility | Location |
|---|---|---|
| **BrowserOS** | Chromium runtime. Shared by Crawl4AI, Delphi MCP, and passive recorder | external process, managed by `BrowserOSAdapter` |
| `BrowserOSAdapter` | Sensor + Motor protocols, BrowserOS lifecycle (start / health check) | `src/automation/adapters/browser_os.py` |
| `Labyrinth` | Portal room atlas (URLNode, RoomState, Skeleton) | `src/automation/ariadne/labyrinth/` |
| `AriadneThread` | Mission transition graph | `src/automation/ariadne/thread/` |
| `Interpreter` | Instruction → mission_id entry point | `src/automation/langgraph/nodes/interpreter.py` |
| `Theseus` | Deterministic fast-path actor | `src/automation/langgraph/nodes/theseus.py` |
| `Delphi` | LLM rescue via BrowserOS MCP | `src/automation/langgraph/nodes/delphi.py` |
| `Recorder` | Trace assimilation into Labyrinth + Thread | `src/automation/langgraph/nodes/recorder.py` |

## State object (`AriadneState`)

Pure data — no live objects. Adapters, Labyrinth, and Thread are constructor-injected into actors, never placed in state.

Key fields:
- `instruction`, `mission_id`, `portal_name` — seeded by Interpreter
- `snapshot`, `current_room_id` — written by Observe/Theseus
- `extracted_data: list[dict]` — typed accumulator for extraction missions (no loose `session_memory` dict)
- `trace: list[TraceEvent]` — append-only, consumed by Recorder
- `agent_failures: int` — Delphi circuit breaker counter
- `errors: list[str]` — append-only

### Known gap — terminal room routing

`builder.py` routing functions only see `AriadneState`. `Labyrinth` is injected into node constructors, not placed in state. This means the router cannot call `room.state.is_terminal` directly.

**Fix needed**: add `is_mission_complete: bool` to `AriadneState`. Theseus writes it `True` when `labyrinth.get_room(room_id).state.is_terminal`. The router reads it instead of querying Labyrinth. No Labyrinth ref needed in routing.

## Persistence

Only `Labyrinth` and `AriadneThread` survive between runs. `AriadneState` is ephemeral — it dies with the graph execution.

**How**: classmethods on the domain objects themselves. No Repository protocol for now — extract one if/when multiple storage backends are needed.

```python
Labyrinth.load(portal_name)          # called by langgraph/builder.py at startup
labyrinth.save()                     # called by Recorder after each expand()

AriadneThread.load(portal, mission)  # called by langgraph/builder.py at startup
thread.save()                        # called by Recorder after each add_step()
```

**Who writes**: `Recorder` — the only node that mutates persistent state. After assimilating a `TraceEvent` it calls `save()` on both objects.

**Who reads**: `langgraph/builder.py` — the composition root. It loads Labyrinth + Thread before assembling the graph and injects them into actors via constructor.

## Recording paths

**Active (LLM-driven)**: `Motor.act()` returns `ExecutionResult` with a `TraceEvent`. Reducer appends it to `state["trace"]`. Recorder assimilates at end of turn into `Labyrinth` + `AriadneThread`. Primary learning path.

**Passive (Chromium/Puppeteer)**: User navigates manually in Chrome → exports Chrome DevTools Recorder session as JSON → `Recorder.ingest_passive_trace(devtools_json)`. Produces a low-level Puppeteer thread that can be promoted to an AriadneThread. Out-of-band, no graph run required. **Status: designed, not in scope for current implementation.**

## Where to read more

| Topic | Where |
|---|---|
| Ontology and design decisions | `plan_docs/design/ariadne-ontology-draft.md` |
| OOP actor architecture | `plan_docs/design/ariadne-oop-architecture.md` |
| Adapter lifecycle | `plan_docs/design/browseros-adapter-lifecycle.md` |
| Canonical repo standards | `STANDARDS.md` |
