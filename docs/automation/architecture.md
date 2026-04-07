# Automation Architecture

Navigation guide to the automation system's current boundaries and implementation homes.

## Core design principle

Portal knowledge and browser execution are separate concerns.

- `src/automation/portals/*/maps/` stores portal-specific flow knowledge as JSON.
- `src/automation/ariadne/models.py` defines the shared semantic language consumed by every motor.
- `src/automation/ariadne/session.py` orchestrates one apply run without owning motor-specific behavior.

That separation means an existing portal map can be replayed through a different motor without changing the map itself.

## Runtime flow

The apply stack now follows this path:

1. CLI parses the request in `src/automation/main.py`.
2. `AriadneSession` loads the portal map and ingest state, then asks `src/automation/portals/*/routing.py` which apply branch is valid.
3. If the route stays onsite, a `MotorProvider` opens a backend-specific `MotorSession`.
4. `AriadneNavigator` evaluates the observed state and decides the next step.
5. The motor session observes the live page and executes the requested step.
6. `AutomationStorage` persists `ApplyMeta` and related artifacts.

## Component map

| Component | Responsibility | Authoritative File |
| :--- | :--- | :--- |
| **Ariadne Map** | Portal knowledge, semantic states, and replay paths | `src/automation/portals/*/maps/` |
| **Common Language** | Backend-neutral Pydantic models for states, paths, steps, and artifacts | `src/automation/ariadne/models.py` |
| **AriadneSession** | Apply orchestrator: map loading, context building, run loop, and persistence wiring | `src/automation/ariadne/session.py` |
| **Portal Routing** | Portal-specific apply branch resolution from enriched ingest state | `src/automation/portals/*/routing.py` |
| **Motor Protocol** | Contracts between Ariadne and each backend (`MotorProvider`, `MotorSession`) | `src/automation/ariadne/motor_protocol.py` |
| **Navigator** | State-aware replay and mission status transitions | `src/automation/ariadne/navigator.py` |
| **Recorder** | Session capture and raw trace persistence for promotion workflows | `src/automation/ariadne/recorder.py` |
| **Normalizer** | Draft trace normalization into canonical Ariadne maps | `src/automation/ariadne/normalizer.py` |
| **Motors** | Backend adapters for Crawl4AI and BrowserOS | `src/automation/motors/` |
| **Persistence** | Artifact and metadata management across scrape/apply flows | `src/automation/storage.py` |

## Where to read more

| Topic | Where |
|---|---|
| Package layout, extension rules, and CLI entry points | `src/automation/README.md` |
| Ariadne domain layer and orchestration details | `src/automation/ariadne/README.md` |
| Motor adapter layer and backend contracts | `src/automation/motors/README.md` |
| Semantic layer concepts and goals | `docs/automation/ariadne_semantics.md` |
| Motor capability and intent registry | `docs/automation/ariadne_capabilities.md` |
| Crawl4AI usage rules | `docs/standards/code/crawl4ai_usage.md` |
| Ingestion boundary rules | `docs/standards/code/ingestion_layer.md` |

## Future work

The main architectural direction is in place. Remaining work is concentrated in:

- richer trace normalization and promotion quality in `src/automation/ariadne/normalizer.py`
- routing and enrichment layers for reliable application targets
- additional motors such as vision-assisted and OS-native execution
