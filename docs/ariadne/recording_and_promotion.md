# Ariadne 2.0: Recording, Storage & Promotion

## 1. The Recording Pipeline (Learning)
The recording pipeline captures raw sessions (Human or Agent) and normalizes them into **Graph Candidates**.

### Pipeline Stages:
1.  **Watch**: Captures MCP tool calls or CDP events.
2.  **Record**: Logs a structured `RawRecordingEvent` timeline.
3.  **Process (Node/Edge Detection)**:
    - **Node Detection**: Compares UI snapshots. If the agent returns to a previously seen state, it correlates them instead of creating a new step.
    - **Edge Detection**: Actions performed between two states become `AriadneEdge` transitions.
    - **Blackboard Extraction**: Captures data extractions (e.g. copying a Job ID) as `extract` rules on the edge.
4.  **Map**: Produces an `AriadneMap` with status `draft`.

## 2. Promotion Lifecycle (Maturity)
Graphs mature from raw traces to production-ready artifacts through a quality gate.

```
draft → verified → canonical
```

- **Draft**: Newly recorded graph. Not yet tested deterministically.
- **Verified**: A draft that has successfully completed a dry-run replay by a deterministic Executor (Crawl4AI or BrowserOS CLI).
- **Canonical**: Approved by an operator. Stored in source control. versioned (v1, v2).

## 3. Storage Layout
Ariadne separates packaged maps (code) from runtime artifacts (data).

### Packaged Maps (Source Control)
```
src/automation/portals/<portal>/maps/
  easy_apply.json  # Latest canonical graph
```

### Runtime Artifacts (Data Plane)
```
data/ariadne/recordings/<session_id>/
  normalized_map.json  # Draft map
  raw_timeline.jsonl   # Append-only event log
  screenshots/         # Evidence per state
```

## 4. Map Resolution
When a session starts, the orchestrator:
1.  Loads the target `AriadneMap`.
2.  Enters at the defined `entry_state`.
3.  Initializes the `AriadneState` (State Graph context).
