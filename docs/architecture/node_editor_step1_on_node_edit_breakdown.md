# Node Editor Step 1 Technical Breakdown

> Status note (2026-03-20): this is a historical implementation-slice breakdown. The node editor has moved beyond this step, and some acceptance criteria below no longer reflect the current sandbox exactly.


## Scope

Implement Step 1 only: **on-node edit affordance** as primary entrypoint for node editing in `/sandbox/node_editor`.

This step does not include auto-layout, radial focus re-layout, or floating-edge geometry changes.

## Goal

Move node editing from sidebar-centric interaction to graph-native contextual interaction.

## Confirmed Behavior (from operator decisions)

1. Primary: floating `Edit` affordance appears on selected/hovered node.
2. Secondary: double-click on node opens edit modal.
3. Sidebar edit trigger is removed from canonical flow.

## Implementation Slices

### Slice A — Selection-aware contextual affordance

- Add node-level UI overlay for selected/hovered node.
- Show compact `Edit` button adjacent to node card.
- Ensure button does not block drag unless explicitly clicked.

**Target file**

- `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx`

### Slice B — Event routing and modal entry

- Wire affordance click to existing `openNodeEditor(nodeId)`.
- Preserve `onNodeDoubleClick` as secondary fast path.
- Keep edit guard rules unchanged (`edit_*` states block pane/unfocus exits).

**Target file**

- `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx`

### Slice C — Sidebar cleanup

- Remove `Edit node` button from sidebar control row.
- Keep sidebar focused on global controls (save/discard/unfocus/filter/add node).

**Target file**

- `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx`

### Slice D — Visual polish and discoverability

- Add styling for contextual edit chip/button (`ne-node-edit-chip` style family).
- Ensure affordance appears on hover and selected state, with subtle transition.
- Maintain readability at normal zoom levels.

**Target file**

- `apps/review-workbench/src/styles.css`

## Acceptance Criteria (Step 1 only)

- S1-AC-01: selecting a node displays contextual `Edit` affordance on/near node.
- S1-AC-02: clicking contextual affordance opens edit modal for that node.
- S1-AC-03: double-click still opens edit modal.
- S1-AC-04: sidebar no longer contains node edit trigger.
- S1-AC-05: drag behavior remains intact when not clicking the affordance.
- S1-AC-06: edit guard behavior remains intact (cannot exit edit via pane click/unfocus).

## Risk Notes

- Overlay hitbox can interfere with drag events if pointer-events are not scoped correctly.
- Affordance position may drift under zoom/pan if not rendered as part of node content.
- Excessive always-on controls can clutter graph; hover/selection gating is required.

## Test Plan

### Manual/Playwright checkpoints

1. Open `/sandbox/node_editor`.
2. Click node -> verify contextual `Edit` appears.
3. Click contextual `Edit` -> modal opens for selected node.
4. Double-click another node -> modal opens.
5. Confirm sidebar has no `Edit node` button.
6. Confirm node drag still works when clicking/dragging node body.
7. Confirm pane click/unfocus does not exit active edit modal.

## Out of Scope for Step 1

- `Layout All` and `Layout Focus Neighborhood`
- focus radial periphery
- floating edges and dynamic handle-angle anchoring
- handle reveal and loose-connection redesign
- view options panel and mode badge enhancements

## Next Step After Step 1

Proceed to Step 2: focus readability tuning (1-hop full visibility + non-neighbor dim policy + optional `Hide non-neighbors` toggle).
