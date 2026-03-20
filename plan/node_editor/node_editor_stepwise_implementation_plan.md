# Node Editor Stepwise Implementation Plan

## Objective

Implement the node-to-node editor UX in small deterministic steps, following confirmed operator decisions and preserving a stable mental map.

Scope for this plan: `/sandbox/node_editor` only (no document-mode integration).

## Decision Baseline (Locked)

1. Edit entrypoint
   - Primary: contextual edit affordance on selected/hovered node
   - Secondary: double-click node
   - Sidebar edit action removed
2. Layout controls
   - `Layout All` + `Layout Focus Neighborhood`
   - Deterministic layout only
3. Focus policy
   - Focused node: fully visible
   - 1-hop neighbors: fully visible and interactive
   - Non-neighbors: dimmed and non-interactive
   - Optional toggle: `Hide non-neighbors`
4. Spatial behavior
   - Smooth animated transitions
   - Preserve map stability over dynamic physics
5. Handle UX
   - Handles visible on hover/selection
   - Multi-side anchors (top/right/bottom/left)
   - Loose connection mode allowed for conceptual mapping
6. Focus geometry
   - Focused node centered
   - Neighbors on deterministic ring
   - Floating-edge style shortest-angle anchor logic

## Workstream Structure

### Phase 0 — Guardrails and Metrics

Deliverables:

- Explicit acceptance checklist split:
  - `Blockers (current phase)`
  - `Later enhancements`
- Lightweight QA matrix linked to requirement IDs

Checks:

- Build passes
- Existing sandbox route still functional

---

### Phase 1 — On-Node Editing Affordance (Highest Impact)

Goal:

- Move editing affordance to node context.

Tasks:

1. Add contextual `Edit` chip/button to selected or hovered node.
2. Keep double-click behavior.
3. Remove sidebar `Edit node` button.
4. Keep modal lifecycle guards (save/discard required).

Acceptance:

- User can open node edit without leaving graph focus.
- Sidebar no longer controls node edit entry.

---

### Phase 2 — Focus Readability Tuning (Fast Win)

Goal:

- Focus mode keeps context while reducing clutter.

Tasks:

1. Enforce 1-hop fully visible/interactable policy.
2. Tune non-neighbor dim level (configurable via sidebar `View Options`).
3. Add `Hide non-neighbors` toggle.

Acceptance:

- No perceived node loss in focus mode.
- Context control available without changing mode.

---

### Phase 3 — Deterministic Layout Controls

Goal:

- Recover readability quickly through explicit controls.

Tasks:

1. Add `Layout All` button (dagre deterministic pass).
2. Add `Layout Focus Neighborhood` (deterministic radial around focus node).
3. Animate position transitions to avoid hard jumps.

Acceptance:

- Same graph state produces same layout result every run.
- Focus-neighborhood layout does not repack entire canvas.

---

### Phase 4 — Handle and Edge Fluidity

Goal:

- Make connection UX feel lighter and more natural.

Tasks:

1. Reveal handles on hover/selection.
2. Add multi-anchor zones (top/right/bottom/left).
3. Enable loose connection mode where appropriate.
4. Implement floating-edge anchor computation with shortest-angle preference.

Acceptance:

- Connections do not feel constrained to rigid left/right wiring.
- Edge paths read naturally in centered focus layouts.

---

### Phase 5 — View Options + Mode Clarity

Goal:

- Improve operator awareness and quick control.

Tasks:

1. Add `View Options` section:
   - focus opacity slider
   - line style options
   - hide non-neighbors toggle
2. Add visible in-canvas mode badge (`Browse`, `Focus`, `Edit`).
3. Allow badge click to return to browse where safe.

Acceptance:

- Current mode is always visible.
- Key display settings are quickly tunable.

---

### Phase 6 — Connection Creation UX Completion

Goal:

- Complete the drag-to-connect flow from spec.

Tasks:

1. Drag to empty canvas opens contextual floating menu.
2. Menu supports:
   - connect to existing node
   - create new node and auto-connect
3. Edge click continues to open relation editing.

Acceptance:

- Users can create relations without long pointer travel.
- Relation creation flow is consistent with focus/edit modes.

## Verification Protocol (Per Phase)

For each phase:

1. Build check: `npm --prefix apps/review-workbench run build`
2. Playwright sanity on `/sandbox/node_editor`
3. Update `docs/ui/node_editor_compliance_matrix.md`
4. Commit with phase identifier in message
5. Changelog entry with exact run/view instructions

## Execution Order Rationale

This order resolves highest-friction interactions first:

1. on-node edit entrypoint
2. focus readability
3. deterministic layout controls
4. handle/edge fluidity
5. visibility and controls polish
6. full contextual relation creation

## Definition of Done (This Plan)

- Phase-by-phase completion tracked with explicit evidence.
- No phase closed without build + Playwright verification.
- Changelog includes exact commands and route for reproduction.
