# Automation Architecture

Navigation guide to the automation system's current boundaries and implementation homes.

## Core design principle

Portal knowledge and browser execution are separate concerns.

- `src/automation/portals/*/maps/` stores portal-specific flow knowledge as JSON.
- `src/automation/ariadne/models.py` defines the shared semantic language consumed by every motor.
- `src/automation/ariadne/session.py` orchestrates one apply run without owning motor-specific behavior.

That separation means an existing portal map can be replayed through a different motor without changing the map itself.

## Runtime flow

The apply stack follows this **LangGraph Flight Controller** orchestration:

1.  **Map Selection**: `AriadneSession` loads the `AriadneMap` (State Graph) for the portal.
2.  **State Observation**: At the current node, the Orchestrator uses a **Capability (Tool)** to identify the UI state.
3.  **Blackboard Initialization**: The `AriadneBlackboard` is initialized with profile and job data.
4.  **JIT Translation**: The Orchestrator selects the next **AriadneEdge** and calls the **JIT Translator** to produce a command for the current action.
5.  **Executor Dispatch**: The **Executor (Motor)** runs the command and returns the outcome.
6.  **Blackboard Update**: If the action extracts data (e.g., Application ID), it is written to the Blackboard.
7.  **Transition**: The Orchestrator moves to the next node in the graph based on the executor's result.
8.  **Recovery**: If the observed state is unexpected, the Orchestrator routes to a **Planner (Agent)** or a **Breakpoint (HITL)** node to recover the flow and update the Blackboard.

## Component map

| Component | Responsibility | Authoritative File |
| :--- | :--- | :--- |
| **Ariadne Map** | Portal State Graph (Nodes & Edges) | `src/automation/portals/*/maps/` |
| **Common Language**| Graph models (Map, State, Edge, Intent) | `src/automation/ariadne/models.py` |
| **State Blackboard**| Read-Write session memory (Memory Layer) | `src/automation/ariadne/blackboard.py` |
| **LangGraph Controller**| Orchestration of the Graph and Cascade | `src/automation/ariadne/graph.py` |
| **JIT Translator** | Compiles single intents into `MotorCommand` | `src/automation/ariadne/translators.py` |
| **Executors** | "Dumb" motors that run commands (Crawl4AI, BrowserOS CLI) | `src/automation/motors/` |
| **Planners** | Autonomous agents for self-healing (LangGraph Agent) | `src/automation/motors/browseros/agent/` |
| **Capabilities** | Tools used by others (Vision, Danger Detection) | `src/automation/ariadne/capabilities/` |

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
