# 05 Validation And Test Impact Map

## Goal

Reduce waste at test time by mapping change impact before implementation.

## Principle

Every planned UI feature should declare:

- touched surfaces
- impacted state contracts
- persistence implications
- rendering implications
- manual verification path

## Core Impact Map

### Editing `NodeEditorSandboxPage.tsx`

Likely impacts:

- sandbox interaction behavior
- local history
- layout actions
- keyboard shortcuts

Usually does not directly impact:

- backend persistence
- CV graph payloads

### Editing `CvGraphEditorPage.tsx`

Likely impacts:

- saved CV graph shape
- container/group behavior
- proxy edges
- API roundtrip correctness

### Editing `RichTextPane.tsx`

Likely impacts:

- annotation creation/editing
- text anchor identity
- doc-to-graph link behavior

### Editing API payloads / models

Likely impacts:

- frontend fetch/save
- persistence compatibility
- existing saved data

## Verification Strategy By Feature Class

- layout/view preset changes
  - verify save/restore
  - verify filters and collapsed state
- node-type registry changes
  - verify all node renderers still mount
- annotation changes
  - verify anchor persistence after edit/save/reload
- explorer changes
  - verify selection sync with graph and document panes

## Acceptance

- every implementation subtask references this file and lists its change impact before coding
