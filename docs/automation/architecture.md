# Automation Architecture

Navigation guide to the automation system's current boundaries and implementation homes.

## Core design principle

Portal knowledge and browser execution are separate concerns.

- `src/automation/portals/*/maps/` stores portal-specific flow knowledge as JSON.
- `src/automation/ariadne/models.py` defines the shared semantic language consumed by every motor.
- `src/automation/ariadne/graph/orchestrator.py` orchestrates one graph-driven run without owning motor-specific behavior.

That separation means an existing portal map can be replayed through a different motor without changing the map itself.

## Runtime flow

The apply stack follows this **LangGraph Flight Controller** orchestration:

1.  **Map Selection**: `MapRepository` loads the `AriadneMap` (State Graph) for the portal.
2.  **State Observation**: At the current node, the Orchestrator uses a **Capability (Tool)** to identify the UI state.
3.  **State Initialization**: `AriadneState` is initialized with profile data, job data, and mission context.
4.  **JIT Translation**: The Orchestrator selects the next **AriadneEdge** and calls the **JIT Translator** to produce a command for the current action.
5.  **Executor Dispatch**: The **Executor (Motor)** runs the command and returns the outcome.
6.  **Session Memory Update**: If the action extracts data (e.g., application metadata or discovery payloads), it is written to `session_memory`.
7.  **Transition**: The Orchestrator moves to the next node in the graph based on the executor's result.
8.  **Recovery**: If the observed state is unexpected, the Orchestrator routes to a **Planner (Agent)** or a **Breakpoint (HITL)** node to recover the flow and update `session_memory`.

## Component map

| Component | Responsibility | Authoritative File |
| :--- | :--- | :--- |
| **Ariadne Map** | Portal State Graph (Nodes & Edges) | `src/automation/portals/*/maps/` |
| **Common Language**| Graph models (Map, State, Edge, Intent) | `src/automation/ariadne/models.py` |
| **Session Memory**| Read-write mission memory | `src/automation/ariadne/models.py` |
| **LangGraph Controller**| Orchestration of the Graph and Cascade | `src/automation/ariadne/graph/orchestrator.py` |
| **JIT Translator** | Compiles single intents into `MotorCommand` | `src/automation/adapters/translators/` |
| **Executors** | "Dumb" motors that run commands (Crawl4AI, BrowserOS CLI) | `src/automation/motors/` |
| **Planners** | Autonomous agents for self-healing (LangGraph Agent) | `src/automation/ariadne/graph/nodes/agent.py` |
| **Capabilities** | Hinting, recording, and related tools | `src/automation/ariadne/capabilities/` |

## Where to read more

| Topic | Where |
|---|---|
| Package layout, extension rules, and CLI entry points | `src/automation/README.md` |
| State graph and orchestration details | `docs/ariadne/architecture_and_graph.md` |
| Executor and translator boundaries | `docs/ariadne/execution_interfaces.md` |
| Mode and portal configuration model | `docs/ariadne/portals_and_modes.md` |
| Recording and promotion lifecycle | `docs/ariadne/recording_and_promotion.md` |
| Canonical repo standards | `STANDARDS.md` |

## Future work

The main architectural direction is in place. Future work should be tracked through `plan_docs/issues/Index.md` instead of this document.
