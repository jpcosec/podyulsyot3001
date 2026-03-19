# Node Editor Behavior Specification

## Status

- Drafted from operator requirements on 2026-03-18.
- Scope is interaction behavior only (no implementation details).

## Intent

Define the canonical interaction model for the graph node editor UI.
This specification prioritizes behavior, visibility rules, and editing flows before further UI implementation.

## Constraints

- The existing document view behavior is preserved as-is; this spec does not redefine document view behavior.
- The editor is a dedicated fullscreen graph workspace with a collapsible sidebar.
- Node and relation presentation is data-driven, explicit, and customizable.

## Core Data Model (Behavioral)

Each node supports:

- `name` (main property, always visible)
- regular editable properties
- optional hover-only properties
- optional always-visible secondary properties (for example counters)
- composition (node can contain child nodes)
- extensible attributes (new attributes can be added)

Each relation supports:

- source node and target node
- relation type
- optional relation attributes

## Visual Mapping Contract

Visuals are mapped from node/relation attributes through explicit, configurable rules.

- Node mapping examples: shape, fill color, border color, border style, size, label badges.
- Relation mapping examples: line color, width, style, arrow marker, label visibility.
- Mapping configuration must be declarative and user-customizable from the editor controls.
- No hidden implicit styling logic; every visual outcome must be traceable to a rule.

## Visibility Layers

### Node property visibility tiers

1. Always visible
   - `name` (required)
   - optional key fields (for example child count)
2. Hover visible
   - selected secondary properties
3. Edit visible
   - complete editable form for node properties and extensible attributes

### Relation visibility tiers

- Global: show all or show selected relation types only
- Focused: show only relations connected to selected node
- Contextual: hide, fade, or disable interaction on non-target relations

## Interaction Modes

### Editor State Model

The editor runs with one active state at a time:

- `browse`
- `focus`
- `edit_node`
- `edit_relation`

Transition rules:

- `browse -> focus`: user focuses a node.
- `focus -> edit_node`: user enters node editing for the focused node.
- `focus -> edit_relation`: user selects a relation for editing.
- `edit_node -> focus` or `edit_relation -> focus`: user closes editor after save/discard.
- `focus -> browse`: user unfocuses/reset focus.

Guard rule:

- Leaving `edit_node` or `edit_relation` is blocked until pending changes are resolved by save or discard.

### Selection Model

- Single selection by default (one node or one relation at a time).
- Relation selection clears node selection.
- Node selection clears relation selection.
- Canvas background click clears current selection and returns to `browse` when no focus lock is active.
- Multi-select is out of scope for this draft.

### [A] Browse mode

- User navigates and inspects nodes.
- Hover reveals hover-tier properties.
- Container nodes are initially collapsed to name-first summaries.
- All visible nodes remain draggable if they are free nodes.

### [B] Focus mode

When focusing a node, configurable behavior options include:

- center and zoom to focused node
- dim non-focused nodes
- hide non-focused nodes
- make non-focused nodes unreachable (non-interactive)
- show only selected relation types
- show only relations attached to focused node

Focus behavior must be togglable and composable (multiple options can be active together).
Default focus behavior:

- center + zoom to focused node
- fade non-focused nodes
- keep non-focused nodes non-interactive until unfocus

### [C] Edit mode

- Selecting a node enables property and relation editing for that node.
- For this node-to-node phase, editing opens an overlay modal form.
- Node form supports existing properties and newly added attributes.
- Selecting any relation line opens relation inspection.
- If a relation is editable, relation type and relation attributes can be edited.

## Edit and Save Lifecycle

- Any node/relation field update marks the workspace as `dirty`.
- Save is explicit (user-triggered), not implicit.
- Save persists:
  - node properties and extensible attributes
  - relation type and relation attributes
  - relation endpoints after reconnect operations
  - graph layout positions for free nodes
  - expanded/collapsed composition state
  - active mapping configuration and visibility controls for the workspace
- Cancel in edit mode closes the editor panel and keeps changes only if already saved.
- Discard reverts unsaved edits for the active node/relation and clears `dirty` if no other unsaved changes exist.
- Validation errors must block save and show the failing fields.

## Composition Behavior

- A node can contain nodes of same or different categories.
- Container nodes (for example CV sections like Education) start collapsed and show summary info.
- Internal composition can be inspected in two ways:
  - hover preview
  - explicit expand/collapse
- Expanded view must keep child items clearly linked to the parent container.
- Collapsed children are not directly editable until expanded or opened through container navigation.
- Relations to collapsed children are hidden by default and shown when the container is expanded.

## Node and Relation Manipulation

- Free (non-contained) nodes are draggable for manual arrangement.
- Nodes expose handles for connecting relations.
- Unrelated nodes can be connected by dragging from sidebar sections into the canvas and linking.
- Relation creation/editing must support both:
  - simple un-attributed relations
  - attributed relations editable from edge selection
- Relation lifecycle actions:
  - create relation (drag handle)
  - inspect relation (click edge)
  - edit relation type and attributes
  - reconnect relation endpoint(s)
  - delete relation
- Node lifecycle actions:
  - create node
  - edit node
  - reposition free node
  - delete node (with explicit confirmation and relation impact warning)

## Workspace Layout

- Fullscreen canvas workspace (neutral background; exact color is not constrained).
- Collapsible sidebar controls:
  - add node
  - show/hide relation types
  - save
  - unfocus/reset focus
  - filter nodes by selected fields
  - expose candidate nodes for new connections

`candidate nodes` means nodes currently eligible to receive a new relation from the selected node under active type/filter constraints.

## Required UX Outcomes

- Name-first readability at all times.
- Clear switch between browse, focus, and edit behavior.
- Predictable graph visibility under filters/focus.
- Composition is understandable without opening every node.
- Relation editing is discoverable from edge interaction.

## Priority Rules (Conflict Resolution)

When multiple controls are active, apply precedence in this order:

1. Edit mode constraints
2. Focus mode constraints
3. Relation type visibility filters
4. Node field filters
5. Hover visibility

This order avoids ambiguity when a node is both filtered and focused.

Additional guarantee:

- An actively edited node or relation stays visible and interactive regardless of active filters until the edit session ends.

## Out of Scope (Current Draft)

- Backend schema details and persistence protocol
- Keyboard shortcut design
- Permission model and multi-user collaboration
- Rendering library-specific implementation decisions

## Sandbox Requirement

This behavior model must be represented in a dedicated sandbox surface, isolated from other experimental views, so each interaction mode can be validated independently.

Sandbox route: `/sandbox/node_editor`

## Acceptance Checklist

Each assertion must be independently verifiable in the sandbox using mock graph data (not real CV data).

### Visibility

- [ ] AC-01: Every node shows `name` at all times, regardless of zoom or state.
- [ ] AC-02: Hovering a node reveals hover-tier properties; leaving hides them.
- [ ] AC-03: A container node starts collapsed showing name + child count only.
- [ ] AC-04: Expanding a container reveals its child nodes linked to the parent.

### Browse mode

- [ ] AC-05: Free nodes are draggable; contained nodes are not.
- [ ] AC-06: Clicking canvas background clears selection and returns to browse state.

### Focus mode

- [ ] AC-07: Focusing a node centers + zooms to it, fades non-focused nodes, and makes them non-interactive.
- [ ] AC-08: Sidebar unfocus/reset returns to browse with all nodes restored.
- [ ] AC-09: Only relations attached to the focused node are visible; others are hidden or faded.

### Edit mode

- [ ] AC-10: Selecting a focused node opens an overlay modal form for property editing.
- [ ] AC-11: Editing any field marks the workspace as dirty; Save button activates.
- [ ] AC-12: Discard reverts unsaved changes; dirty indicator clears if no other pending edits.
- [ ] AC-13: Leaving edit mode is blocked while unsaved changes exist (guard rule).

### Relations

- [ ] AC-14: Clicking a relation line opens relation inspection (and editing if attributes exist).
- [ ] AC-15: Sidebar relation-type toggle hides/shows edges by type.
- [ ] AC-16: Dragging a handle from one node to another creates a new relation.

### Visual mapping

- [ ] AC-17: Changing a mapping rule (for example node category to fill color) updates the canvas immediately.

### Conflict resolution

- [ ] AC-18: An actively edited node stays visible and interactive even when filters would normally hide it.
