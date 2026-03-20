# Node Editor Feedback: Doubts and Gaps

> Status note (2026-03-20): this is now a historical gap-tracking document. Several gaps described below have already been implemented in the sandbox, so read it as design-history/context rather than current status.


## Context

This document captures open doubts and implementation gaps raised from operator feedback on the node-to-node sandbox.

Reference surfaces:

- Spec: `docs/architecture/node_editor_behavior_spec.md`
- Compliance matrix: `docs/architecture/node_editor_compliance_matrix.md`
- Current sandbox: `/sandbox/node_editor`

## Point-by-Point Doubts and Gaps

### 1) "Why is Edit node in the sidebar? Shouldn't it be in the node once selected?"

**Doubt**

- Should edit entry be primary on-node (contextual affordance) with sidebar as secondary fallback?
- Should double-click remain as a hidden power action only, while visible edit is in-node?

**Gap in current implementation**

- Edit action is anchored in sidebar controls, not in-node contextual UI.
- No visible on-node edit affordance after selection.

**Impact**

- Discoverability is weaker.
- Interaction feels "control-panel-driven" instead of graph-native.

**Decision needed**

- Confirm canonical edit trigger order:
  1. on-node edit button (primary)
  2. double-click (secondary)
  3. sidebar edit (fallback)

---

### 2) "Where are the autoorganize buttons?"

**Doubt**

- Should auto-organize affect full graph only, or support two scopes (full graph + focus neighborhood)?
- Should layout be deterministic (same input -> same output) or "organic" each run?

**Gap in current implementation**

- No `Auto-Layout` control exists in sidebar.
- Node placement is mostly manual drag and static seed positions.

**Impact**

- Graph readability degrades as node count grows.
- Harder to recover a clean visual state after edits.

**Decision needed**

- Confirm an explicit `Auto-Layout` button with at least:
  - `Layout All`
  - `Layout Focus Neighborhood`

---

### 3) "Why on focus I lose the nodes my node is related to?"

**Doubt**

- Is the issue true loss (hidden) or extreme dimming causing perceived loss?
- Should first-degree neighbors always stay clearly visible and interactive?

**Gap in current implementation**

- Focus mode applies aggressive dimming and interaction restrictions.
- Visibility/intensity settings are not user-tunable.

**Impact**

- Focus mode can feel too isolating.
- User loses broader graph context during inspection.

**Decision needed**

- Confirm default focus policy:
  - focus node: fully visible
  - 1-hop neighbors: fully visible
  - non-neighbors: faded (not hidden)
  - optional toggle for "hide non-neighbors"

---

### 4) "Spatial ordering should be more liquid"

**Doubt**

- Does "liquid" mean animated transitions only, or dynamic force-like arrangement during interaction?
- Should spatial behavior optimize stability (preserve mental map) or readability (repack often)?

**Gap in current implementation**

- Positioning logic is rigid and mostly static.
- No explicit focus-centered peripheral arrangement strategy.

**Impact**

- Layout feels mechanical and less intuitive under repeated focus shifts.

**Decision needed**

- Confirm a focus-centered radial neighborhood policy:
  - focused node at center
  - related nodes around periphery
  - smooth animated transitions

---

### 5) "Why do we have 2 fixed handles? Is that obligatory?"

**Doubt**

- Should handles be visible only on hover/selection to reduce visual noise?
- Should connections be directional by default or loose/bidirectional for this phase?

**Gap in current implementation**

- Uses fixed left/right handles only.
- No configurable handle strategy (dynamic positions, multiple handles, or loose mode).

**Impact**

- Interaction may feel rigid.
- Connection start/end affordances may not match user mental model.

**Decision needed**

- Confirm preferred connection UX baseline for this phase:
  - hover-revealed handles
  - optional `ConnectionMode.Loose`
  - multiple handle zones (top/right/bottom/left)

---

### 6) "Handle location should be more liquid; focus centers node and others on periphery"

**Doubt**

- Should peripheral placement be pure deterministic radial or simulation-based?
- Should peripheral ordering be based on edge type, edge weight, or simple angular distribution?

**Gap in current implementation**

- No dedicated focused-periphery layout mode.
- Handle placement does not adapt to focus geometry.

**Impact**

- In-focus relation reading is less immediate.
- Dense neighborhoods can produce awkward edge geometry.

**Decision needed**

- Confirm focused layout contract:
  - center focused node
  - ring for direct neighbors
  - optional second ring for related-but-not-direct nodes
  - handle side preference derived from relative node angle

## Cross-Cutting Gaps

### A) Missing interaction configuration panel

- No place to tune focus behavior (fade/hide/non-interactive policy).
- No place to tune connection style (strict vs loose, handle visibility).

### B) Missing explicit UX mode indicators

- State is present, but mode transitions are not sufficiently self-explanatory in-canvas.

### C) Missing phased acceptance split

- Current acceptance list mixes immediate node-to-node goals with later UX refinements.
- Need "Phase-now blockers" vs "Phase-later enhancements" grouping.

## Proposed Resolution Workflow

1. Confirm decisions listed per point above.
2. Update `docs/architecture/node_editor_behavior_spec.md` with resolved defaults.
3. Regenerate `docs/architecture/node_editor_compliance_matrix.md` against resolved defaults.
4. Implement in `/sandbox/node_editor` in small increments with Playwright verification each increment.

## Suggested Immediate Priority Order

1. On-node edit affordance (Point 1)
2. Focus readability policy tuning (Point 3)
3. Auto-layout controls (Point 2)
4. Focus radial/periphery layout (Points 4 and 6)
5. Handle UX redesign (Point 5)
