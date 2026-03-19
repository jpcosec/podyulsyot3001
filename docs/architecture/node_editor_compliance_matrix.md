# Node Editor Compliance Matrix (Node-to-Node Phase)

## Purpose

This document compares the current `/sandbox/node_editor` behavior against the proposed UI/UX specification for the node-to-node phase.

Scope is intentionally limited to simple nodes, node-to-node relations, and editable properties.

## How To Verify

1. Start stack: `./scripts/dev-all.sh`
2. Open sandbox: `http://127.0.0.1:4173/sandbox/node_editor`
3. Compare behavior with this matrix and the source spec:
   - `docs/architecture/node_editor_behavior_spec.md`

## Status Legend

- `Pass`: implemented and observable in current sandbox
- `Partial`: implemented in part, but not fully aligned with spec
- `Missing`: not implemented yet

## Requirement Matrix

| ID | Section | Requirement | Status | Evidence | Notes |
|---|---|---|---|---|---|
| WS-01 | Workspace | Fullscreen neutral canvas with pan/zoom | Partial | `apps/review-workbench/src/styles.css:1217` | Uses `height: calc(100vh - 48px)` with shell offsets, not true fullscreen from viewport edge |
| WS-02 | Workspace | Collapsible sidebar | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:586` | Sidebar toggle + collapsed state implemented |
| WS-03 | Workspace | Edge panning near viewport borders while dragging | Missing | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:659` | No explicit edge-panning behavior configured |
| BR-01 | Browse | Browse shows summarized nodes and allows free arrangement | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:269` | Nodes draggable in browse mode |
| BR-02 | Browse | Hover reveals secondary properties | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:161` | Tooltip built from node properties |
| FO-01 | Focus | Click focuses node and camera centers/zooms | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:361` | `fitView` on focused node |
| FO-02 | Focus | Non-related nodes/edges dim, direct relations emphasized | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:273` | Neighbor-based active set + edge dimming |
| FO-03 | Focus | Clicking another node switches focus | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:347` | `onNodeClick` reassigns focus |
| ED-01 | Edit | Double click or edit action opens modal overlay | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:366` | Double click + focus edit path available |
| ED-02 | Edit | Exit edit only via Save/Discard | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:380` | Pane/unfocus blocked during edit state |
| ED-03 | Edit | Typed field mapping (`string`, `text`, `number`, `date`, `boolean`, `enum`, `enum_open`) | Partial | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:687` | String/select exists; full typed map pending |
| ED-04 | Edit | Dynamic attributes require name + type before value input | Partial | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:714` | Dynamic key/value exists; explicit type step missing |
| ED-05 | Edit | Internal relations visible as pills in modal with remove action | Missing | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:684` | Relation-pill list not implemented |
| CO-01 | Connections | Drag handle to empty canvas opens contextual floating menu | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:457` | `onConnectStart` + `onConnectEnd` now open menu on empty drop |
| CO-02 | Connections | Context menu supports connect-existing and create+connect-new | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:487` | Menu supports existing node connect and create+connect with immediate edit modal |
| CO-03 | Connections | Clicking relation opens inspection/editing | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:373` | Edge click opens relation modal |
| SB-01 | Sidebar | Dirty, Save Workspace, Discard/Reset, Unfocus, Auto-Layout | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:699` | `Layout all` and `Layout focus` controls implemented |
| SB-02 | Sidebar | Drag-and-drop creation palette | Missing | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:616` | Add button only, no DnD palette |
| SB-03 | Sidebar | Relation toggles + text and attribute filters | Partial | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:633` | Relation toggle + text filter exist; attribute filter missing |
| SB-04 | Sidebar | Minimap for large graph navigation | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:675` | Minimap enabled |
| PR-01 | Priority Rules | Edit mode precedence over all other visibility logic | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:380` | Guards block interactions in edit mode |
| PR-02 | Priority Rules | Focus restrictions precede relation/node filter behavior | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:273` | Focus active set computed first |
| PR-03 | Priority Rules | Relation-type filter precedes node-attribute filters | Partial | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:256` | Attribute filter step not present yet |

## Coverage Summary

- Total requirements: 23
- Pass: 16
- Partial: 5
- Missing: 2
- Weighted score: 80%

Formula: `(Pass + 0.5 * Partial) / Total * 100`

## Next Priority Fixes

1. Expand typed field rendering strategy in edit modal (`ED-03`)
2. Add typed dynamic-attribute creation flow (`ED-04`)
3. Add DnD creation palette (`SB-02`)
4. Add relation pills in node edit modal (`ED-05`)
5. Add explicit edge panning behavior (`WS-03`)
