# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Commands

```bash
# Run all automation tests
python -m pytest tests/unit/automation/ -q

# Run a single test file
python -m pytest tests/unit/automation/ariadne/test_session.py -v

# Scrape jobs from a portal
python -m src.automation.main scrape --source <stepstone|xing|tuberlin> --limit <n>

# Apply to a job (BrowserOS default motor)
python -m src.automation.main apply --source <xing|stepstone|linkedin> --job-id <id> --cv <path>

# Dry-run apply (no submission)
python -m src.automation.main apply --source xing --job-id <id> --cv <path> --dry-run

# Set up a portal session (manual login in BrowserOS)
python -m src.automation.main apply --source xing --setup-session

# Verify BrowserOS runtime
python -m src.automation.main browseros-check

# Promote a recorded trace to a canonical map
python -m src.automation.main promote --trace-id <id> --portal <name>
```

## Architecture

The system uses the **Ariadne Semantic Layer** to decouple portal logic from execution engines.

### Data Flow

```
Recording (OpenBrowser agent) → AriadneSessionTrace
                                        ↓
                           AriadneNormalizer.normalize()
                                        ↓
             AriadnePortalMap (JSON at portals/<portal>/maps/<flow>.json)
                                        ↓
                           AriadneSession.run(motor, ...)
                                        ↓
                   Motor: BrowserOSMotorProvider | C4AIMotorProvider
```

### Key Layers

**`src/automation/ariadne/`** — Backend-neutral brain:
- `models.py`: Core types — `AriadnePortalMap`, `AriadneState`, `AriadnePath`, `AriadneStep`, `AriadneTarget`, `AriadneIntent` (CLICK, FILL, UPLOAD), `JobPosting`, `ApplyMeta`.
- `session.py`: `AriadneSession` — the top-level apply orchestrator. Loads the portal map, resolves routing, calls `AriadneNavigator`, dispatches steps to the motor, handles HITL interrupts and danger signals.
- `navigator.py`: `AriadneNavigator` — state-aware path traversal with recovery (finds current state via `presence_predicate` CSS selectors).
- `motor_protocol.py`: `MotorProvider` and `MotorSession` Protocols — the interface motors must implement.
- `danger_detection.py` + `danger_contracts.py`: Safety guards that run before submission to detect risky states.
- `hitl.py`: Human-in-the-loop pause/resume logic with persisted `ApplyInterruptRecord`.
- `recorder.py` + `trace_models.py`: Raw session capture, written to `data/ariadne/recordings/<trace_id>/trace_manifest.json`.
- `normalizer.py`: `AriadneNormalizer` — converts a raw `AriadneSessionTrace` into a canonical `AriadnePortalMap`.
- `job_normalization.py`: Normalizes `JobPosting` fields (titles, employment types) to canonical forms.

**`src/automation/portals/`** — Portal maps and routing:
- `<portal>/maps/easy_apply.json`: The single canonical `AriadnePortalMap` for a portal's apply flow.
- `<portal>/routing.py`: Determines if an apply stays onsite or redirects externally (wraps `portals/routing.py`).
- `portals/routing.py`: Shared `resolve_portal_routing()` dispatcher.

**`src/automation/motors/`** — Execution backends:
- `browseros/` (port 9200): Direct MCP tool calls with fuzzy `text`-based targeting. Uses `BrowserOSMotorProvider` → `cli/backend.py`. The `agent/` subdirectory contains the OpenBrowser LLM agent used during recording.
- `crawl4ai/` (injected into BrowserOS port 9101): Compiles `AriadnePath` → `C4AI IR` → `C4A-Script`. Pipeline: `compiler/compiler.py` → `compiler/ir.py` → `compiler/serializer.py`. Portal-specific scrapers live at `crawl4ai/portals/<portal>/scrape.py`.
- `vision/` + `os_native_tools/`: Stub motor providers for screenshot-based and native-OS interaction.

**`src/automation/`** root:
- `main.py`: CLI dispatcher — `scrape`, `apply`, `browseros-check`, `promote`.
- `contracts.py`: `CandidateProfile`, `ApplyJobContext`, `ExecutionContext` — cross-boundary typed payloads.
- `storage.py`: `AutomationStorage` — all file I/O for artifacts, traces, and results (wraps `src/core/data_manager.py`).
- `credentials.py`: `CredentialStore` / `ResolvedPortalCredentials` — env-var-based credential resolution.

### BrowserOS Runtime

BrowserOS is an external AppImage (`/home/jp/BrowserOS.AppImage --no-sandbox`).

| Endpoint | Default |
|---|---|
| Base | `http://127.0.0.1:9000` |
| MCP | `http://127.0.0.1:9000/mcp` |
| Chat | `http://127.0.0.1:9000/chat` |

Override with `BROWSEROS_BASE_URL`. Fallback extraction order controlled by `AUTOMATION_EXTRACTION_FALLBACKS` (default: `browseros`).

## Development Principles

1. **Ariadne First**: New portals/flows must start as `AriadnePortalMap` JSON. No hardcoded motor logic.
2. **Backend Neutrality**: Actions use `AriadneIntent` (CLICK, FILL, UPLOAD); `AriadneTarget` carries both `css` (Crawl4AI) and `text` (BrowserOS fuzzy match).
3. **States & Transitions**: Use `AriadneState` with `presence_predicate` so the navigator can recover from deviations.
4. **Recording → Promotion workflow**: Record with `AriadneRecorder` via OpenBrowser agent → normalize with `AriadneNormalizer` → `promote` CLI writes canonical JSON map.

## Key Documentation

- Ariadne architecture: `docs/automation/ariadne_semantics.md`
- Capability registry: `docs/automation/ariadne_capabilities.md`
- BrowserOS setup: `docs/automation/browseros_setup.md`
- Original design spec: `docs/superpowers/specs/2026-04-06-unified-automation-refactor-design.md`
