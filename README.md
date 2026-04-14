# Ariadne Automation — Unified Worktree

LangGraph-based browser automation system. Uses a **Sense-Think-Act** loop over a persistent semantic layer
(`Labyrinth` + `AriadneThread`) that accumulates portal knowledge across runs.

---

## Navigation

This repo uses READMEs as an **indexation system**, not as comprehensive documentation.

| Topic | Where |
|---|---|
| Architecture, ontology, data flow | [`docs/automation/architecture.md`](docs/automation/architecture.md) |
| BrowserOS adapter lifecycle | [`plan_docs/design/browseros-adapter-lifecycle.md`](plan_docs/design/browseros-adapter-lifecycle.md) |
| Workflow and coding standards | [`STANDARDS.md`](STANDARDS.md) |
| Agent role protocols | [`AGENTS.md`](AGENTS.md) |
| Change history | [`changelog.md`](changelog.md) |

---

## Source Layout

```
src/automation/
│
├── contracts/          # Layer 0 — shared types, no internal imports
│   ├── sensor.py       #   Sensor protocol + SnapshotResult
│   ├── motor.py        #   Motor protocol + MotorCommand + TraceEvent + ExecutionResult
│   └── state.py        #   AriadneState (LangGraph TypedDict)
│
├── adapters/           # Layer 1 — physical I/O
│   └── browser_os.py   #   BrowserOSAdapter (Crawl4AI → BrowserOS CDP)
│
├── ariadne/            # Layer 2 — domain
│   ├── labyrinth/      #   Portal atlas (URLNode, RoomState, Skeleton, Labyrinth)
│   ├── thread/         #   Mission transition graph (Action, AriadneThread)
│   └── extraction/     #   PortalDictionary + schema_builder
│
└── langgraph/          # Layer 3 — LangGraph wiring
    ├── nodes/          #   interpreter, observe, theseus, delphi, recorder
    └── builder.py      #   Assembles and returns the compiled graph
```

**Dependency rule** — each layer may only import from the layer above (lower number), never below:

```
contracts  ←  adapters  ←  ariadne  ←  graph
```

---

## Runtime

BrowserOS must be running before any automation session starts.

```bash
# Launch BrowserOS (provides the Chromium instance)
"$BROWSEROS_APPIMAGE_PATH" --no-sandbox

# Verify the MCP health endpoint
curl http://localhost:9100/health
```

Crawl4AI connects to BrowserOS via CDP on port 9000 — no separate browser is launched.

---

## Tests

```bash
python -m pytest tests/ariadne tests/langgraph --asyncio-mode=auto -v
```

Tests mirror the `src/` structure under `tests/` (not `tests/unit/`):

```
tests/
├── ariadne/
│   └── labyrinth/      # test_url_node, test_skeleton, test_labyrinth
│   └── thread/         # test_thread
└── graph/
    └── nodes/          # test_interpreter, test_observe, test_theseus, test_delphi, test_recorder
```

---

## Environment

```env
BROWSEROS_APPIMAGE_PATH="/path/to/BrowserOS.AppImage"
GOOGLE_API_KEY="your_gemini_key"
```
