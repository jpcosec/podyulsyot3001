# 01 Graph Foundations

## Goal

Stabilize the graph editor core so later features do not force repeated rewrites.

## Status

Partial.

- editor state exists
- custom nodes exist
- layout actions exist
- local history exists in sandbox
- persistence is fragmented between sandbox-local and CV-graph API

## This Node Covers

- canonical graph workspace state
- separation between graph data, view state, and external references
- shared contracts across sandbox and structured editors

## Depends On

- `00_status_matrix.md`

## Enables

- `01a_layout_and_view_presets.md`
- `01b_node_type_registry_and_modes.md`
- `01c_editor_state_and_history_contract.md`

## Required Decisions

1. One shared editor state contract for all graph surfaces.
2. Separate domain graph from UI view state.
3. Track viewport, filters, collapsed state, and layout preset independently from node content.
4. Keep annotation anchors as references, not inline ad hoc UI-only blobs.
5. Enforce referential integrity so `graph_view` never keeps dead node/edge/container IDs after `graph_content` mutations.

## Proposed State Layers

- `graph_content`
  - nodes
  - edges
  - typed payloads
- `graph_view`
  - viewport
  - selected/focused ids
  - collapsed containers
  - visible relation types
  - active layout preset
- `graph_history`
  - semantic actions only
- `external_refs`
  - document refs
  - datasource refs
  - schema refs
  - annotation refs

## What Breaks If Edited

- `NodeEditorSandboxPage.tsx`
- `CvGraphEditorPage.tsx`
- API payload mapping if graph content shape changes
- any future explorer panel that assumes node data is self-contained

## Libraries / Patterns

- current: React Flow state hooks are enough
- likely next: `zustand` for shared editor store if multiple surfaces need synchronized state
- React Flow UI patterns can help for node chrome, controls, and search, but not for the state model itself

## State Invariants

- `graph_content` is the durable editor truth.
- `graph_view` is ephemeral and must be pruned whenever `graph_content` deletes or rewrites referenced IDs.
- saved presets must be sanitized on load so missing IDs do not crash rendering.
- Zustand selectors must stay slice-specific to avoid broad re-renders.

## Acceptance

- one written graph state contract exists
- sandbox and CV editor can map into it without ambiguity
- layout presets and rich content nodes can be added without redefining the storage model
- deleting content automatically prunes stale selection, focus, collapsed-state, and saved-preset references
