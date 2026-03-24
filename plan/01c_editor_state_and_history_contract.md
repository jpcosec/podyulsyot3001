# 01c Editor State And History Contract

## Goal

Define what user actions are undoable, what is view-only, and how semantic history interacts with persistence.

## Status

Partial.

- sandbox tracks semantic history for create/edit/delete/connect
- layout and ordering are intentionally not in undo history
- no shared history contract across graph surfaces

## Depends On

- `01_graph_foundations.md`

## Enables

- `03_rich_content_nodes.md`
- `04_external_data_and_schema_integration.md`

## Semantic Action Families

- create node
- delete node
- edit node payload
- create relation
- delete relation
- edit relation payload
- attach external reference
- detach external reference
- create annotation anchor
- delete annotation anchor

## View-Only Actions

- pan / zoom
- reorder by preset
- fit view
- temporary selection state

## Recommendation

- keep semantic history separate from view preset history
- add action metadata:
  - `actor`
  - `timestamp`
  - `surface`
  - `affected_ids`
  - `undo_payload`
  - `redo_payload`

## What Breaks If Edited

- keyboard shortcuts
- delete confirmation logic
- save/discard behavior
- future collaboration or review audit surfaces

## Acceptance

- all graph surfaces use the same semantic action taxonomy
- action logs can be reviewed independently from the canvas state
