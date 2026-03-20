# Node Editor Customization and Architecture

> Status note (2026-03-20): this guide is mostly current, but some source-path references and UI details can drift as the sandbox evolves. Treat it as an operator-oriented architecture guide for the current sandbox, not a strict compliance source.


This is a short operator-oriented guide for the sandbox node editor at `/sandbox/node_editor`.

## Scope at a glance

- Frontend editor sandbox implementation: `apps/review-workbench/src/sandbox/pages/NodeEditorSandboxPage.tsx`
- Node editor behavior contract: `docs/architecture/node_editor_behavior_spec.md`
- Review API endpoints for CV graph payloads: `src/interfaces/api/routers/portfolio.py`
- CV graph read/write model builder: `src/interfaces/api/read_models.py`

## How it works (current architecture)

### 1) Frontend runtime (sandbox)

- The editor is a single React Flow page (`NodeEditorInner`) with local state for nodes, edges, filters, focus, edit drafts, and save/discard snapshots.
- Core state machine is `EditorState = "browse" | "focus" | "edit_node" | "edit_relation"`.
- React Flow state is managed with `useNodesState` and `useEdgesState`.
- Render output is derived through two pipelines:
  - `displayNodes`: applies filter/focus/edit visibility and interactivity.
  - `displayEdges`: applies relation-type filtering + focus dim/hide behavior.
- Save/discard in the sandbox is workspace-local (snapshot compare via `serializeGraph`) and does not call backend APIs.

### 2) Focus and connect behavior

- Focus neighbor graph is computed by `neighborsForNode`.
- Default focus UX now starts with `hideNonNeighbors = true`.
- The `Vacant nodes` drawer computes candidates from non-connected nodes under active constraints (`vacantCandidateNodes`) and creates links with `onConnectFromVacantDrawer`.
- This means you can still connect to currently hidden non-neighbors from the drawer while focused.

### 3) Layout behavior

- `Layout all` uses deterministic Dagre (`layoutAllDeterministic`).
- `Layout focus` uses deterministic radial arrangement around focused node (`layoutFocusNeighborhood`).
- `Layout custom` restores saved manual ordering from a pre-layout position snapshot (`snapshotNodePositions` + `applySavedNodePositions`).

### 4) Backend (where graph data comes from)

- API endpoints:
  - `GET /api/v1/portfolio/base-cv-graph`
  - `GET /api/v1/portfolio/cv-profile-graph`
  - `PUT /api/v1/portfolio/cv-profile-graph`
- Backend payload assembly and persistence are implemented in `read_models.py`:
  - baseline source profile: `data/reference_data/profile/base_profile/profile_base_data.json`
  - saved override file name: `cv_profile_graph_saved.json` (`SAVED_GRAPH_FILENAME`)

## What is configurable vs hardcoded

### Frontend node editor sandbox

Currently hardcoded in `NodeEditorSandboxPage.tsx`:

- Category palette and colors: `CATEGORY_OPTIONS`, `CATEGORY_COLORS`
- Drag templates and defaults: `NODE_TEMPLATES`
- Initial mock graph: `buildInitialGraph`
- Attribute type options in modal forms: `ATTRIBUTE_TYPES`

Configurable at runtime (already supported in UI behavior):

- Relation visibility toggles per active relation type
- Node filtering by name + property key/value
- Focus isolation toggle (`Hide non-neighbors`)
- Deterministic layout commands (`Layout all`, `Layout focus`, `Layout custom`)

### Backend CV graph categories

- Categories are mostly data-driven from profile content and normalized by builder logic (for example `_normalize_skill_category` in `read_models.py`).
- There is no dedicated external config file for category taxonomy yet; behavior is encoded in profile data + normalization code.

## Quick customization cookbook

1. Change available node categories/colors in sandbox
   - Edit `CATEGORY_OPTIONS` and `CATEGORY_COLORS`.
2. Change node templates shown in drag palette
   - Edit `NODE_TEMPLATES`.
3. Change default focus isolation behavior
   - Edit the initial `hideNonNeighbors` state.
4. Change deterministic layout strategy
   - Adjust `layoutAllDeterministic` (Dagre graph params) and/or `layoutFocusNeighborhood`.
5. Change backend skill category normalization
   - Update `_normalize_skill_category` in `src/interfaces/api/read_models.py`.

## How to run and inspect

- Start stack: `./scripts/dev-all.sh`
- Open node editor sandbox: `http://127.0.0.1:4173/sandbox/node_editor`
- API docs (when backend is running): `http://127.0.0.1:8010/docs`
