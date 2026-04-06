# Automation Architecture

Navigation guide to the automation system's design concepts and their implementation homes.

## Core design principle

Portal knowledge (what fields exist, what steps a flow has) is separated from execution mechanics (how to interact with those fields in a browser). The boundary between them is the **Ariadne common language** defined in `src/automation/ariadne/models.py`.

This separation means adding a second execution backend for an existing portal requires no changes to the portal knowledge maps — only a new motor replayer.

## Component Map

| Component | Responsibility | Authoritative File |
| :--- | :--- | :--- |
| **Ariadne Map** | Portal knowledge, semantic states, and paths (JSON) | `src/automation/portals/*/maps/` |
| **Common Language** | The backend-neutral models (Pydantic) | `src/automation/ariadne/models.py` |
| **Navigator** | State-aware replay and recovery logic | `src/automation/ariadne/navigator.py` |
| **Recorder** | Session capture and raw trace persistence | `src/automation/ariadne/recorder.py` |
| **Motors** | Replayers for specific backends (C4A, BrowserOS) | `src/automation/motors/` |
| **Persistence** | Centralized artifact and metadata management | `src/automation/storage.py` |

## Where to read more

| Topic | Where |
|---|---|
| Package layout, boundary rules, data flows, how to extend | `src/automation/README.md` |
| Semantic layer concepts and goals | `docs/automation/ariadne_semantics.md` |
| Motor capability and intent registry | `docs/automation/ariadne_capabilities.md` |
| Crawl4AI usage rules | `docs/standards/code/crawl4ai_usage.md` |
| Ingestion boundary rules | `docs/standards/code/ingestion_layer.md` |

## Future Work (Phase 3+)

The system has graduated to a full semantic model (Phase 2). Future work includes:

- **Promotion Workflow**: Tools to move draft recorded paths to canonical maps.
- **Advanced Recovery**: LLM-assisted state identification when deterministic predicates fail.
- **Multi-Motor Routing**: Automatically switching motors based on task complexity.
- **Vision Motor**: OpenCV-based resolution for non-DOM elements.
