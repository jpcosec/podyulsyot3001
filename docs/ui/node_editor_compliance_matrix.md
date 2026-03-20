# Node Editor Compliance Matrix (Node-to-Node Phase)

> Status note (2026-03-20): this matrix is a useful verification snapshot, but it should not be treated as permanently canonical. Source paths and some pass/partial assumptions can drift as the sandbox changes. Re-verify against the current sandbox before using it as an authoritative status document.


## Purpose

This document compares the current `/sandbox/node_editor` behavior against the proposed UI/UX specification for the node-to-node phase.

Scope is intentionally limited to simple nodes, node-to-node relations, and editable properties.

## How To Verify

1. Start stack: `./scripts/dev-all.sh`
2. Open sandbox: `http://127.0.0.1:4173/sandbox/node_editor`
3. Compare behavior with this matrix and the source spec:
   - `docs/ui/node_editor_behavior_spec.md`

## Status Legend

- `Pass`: implemented and observable in current sandbox
- `Partial`: implemented in part, but not fully aligned with spec
- `Missing`: not implemented yet

## Requirement Matrix

| ID | Section | Requirement | Status | Evidence | Notes |
|---|---|---|---|---|---|
| WS-01 | Workspace | Fullscreen neutral canvas with pan/zoom | Pass | `apps/review-workbench/src/App.tsx:13` | Node-editor route bypasses shell wrapper and uses viewport workspace sizing (`.ne-page` + `.ne-workspace`) |
| WS-02 | Workspace | Collapsible sidebar | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:586` | Sidebar toggle + collapsed state implemented |
| WS-03 | Workspace | Edge panning near viewport borders while dragging | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:583` | Connect-drag pointer tracking with viewport edge auto-pan loop while connecting |
| BR-01 | Browse | Browse shows summarized nodes and allows free arrangement | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:269` | Nodes draggable in browse mode |
| BR-02 | Browse | Hover reveals secondary properties | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:161` | Tooltip built from node properties |
| FO-01 | Focus | Click focuses node and camera centers/zooms | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:361` | `fitView` on focused node |
| FO-02 | Focus | Non-related nodes/edges dim, direct relations emphasized | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:273` | Neighbor-based active set + edge dimming |
| FO-03 | Focus | Clicking another node switches focus | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:347` | `onNodeClick` reassigns focus |
| ED-01 | Edit | Double click or edit action opens modal overlay | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:366` | Double click + focus edit path available |
| ED-02 | Edit | Exit edit only via Save/Discard | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:380` | Pane/unfocus blocked during edit state |
| ED-03 | Edit | Typed field mapping (`string`, `text`, `number`, `date`, `boolean`, `enum`, `enum_open`) | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:204` | Node/relation property rows render type-aware controls (`text_markdown`, `datetime`, and others) |
| ED-04 | Edit | Dynamic attributes require name + type before value input | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:1454` | Each dynamic property row requires explicit key + type fields before save |
| ED-05 | Edit | Internal relations visible as pills in modal with remove action | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:565` | Node modal lists connected relations and stages remove actions until node Save |
| CO-01 | Connections | Drag handle to empty canvas opens contextual floating menu | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:457` | `onConnectStart` + `onConnectEnd` now open menu on empty drop |
| CO-02 | Connections | Context menu supports connect-existing and create+connect-new | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:487` | Menu supports existing node connect and create+connect with immediate edit modal |
| CO-03 | Connections | Clicking relation opens inspection/editing | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:373` | Edge click opens relation modal |
| SB-01 | Sidebar | Dirty, Save Workspace, Discard/Reset, Unfocus, Auto-Layout | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:699` | `Layout all` and `Layout focus` controls implemented |
| SB-02 | Sidebar | Drag-and-drop creation palette | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:961` | Sidebar template chips are draggable and create nodes on canvas drop |
| SB-03 | Sidebar | Relation toggles + text and attribute filters | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:1375` | Sidebar supports per-relation-type toggles, name filter, property-key filter, and property-value matching |
| SB-04 | Sidebar | Minimap for large graph navigation | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:675` | Minimap enabled |
| SB-05 | Sidebar | Vacant nodes drawer for candidate connection targets | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:1480` | Sidebar exposes focus-scoped vacant candidates and supports one-click connect |
| PR-01 | Priority Rules | Edit mode precedence over all other visibility logic | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:380` | Guards block interactions in edit mode |
| PR-02 | Priority Rules | Focus restrictions precede relation/node filter behavior | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:715` | Focus/edit modes bypass node filters first, then focus visibility rules apply |
| PR-03 | Priority Rules | Relation-type filter precedes node-attribute filters | Pass | `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx:732` | Edge visibility is computed by relation-type gate first, then node filter constraints |

## Coverage Summary

- Total requirements: 24
- Pass: 24
- Partial: 0
- Missing: 0
- Weighted score: 100%

Formula: `(Pass + 0.5 * Partial) / Total * 100`

## Next Priority Fixes

All tracked node-to-node requirements in this matrix are currently marked `Pass`.
