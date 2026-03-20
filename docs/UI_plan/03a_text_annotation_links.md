# 03a Text Annotation Links

## Goal

Connect graph nodes to anchored text spans in a reusable, stable way.

## Status

Partial.

- text tagging exists
- view-level linking exists conceptually
- there is no shared graph anchor model

## Depends On

- `03_rich_content_nodes.md`

## Candidate Libraries

- existing `RichTextPane.tsx` for MVP reuse
- `CodeMirror 6` if richer anchor/decorations are needed later
- `Lexical` only if text becomes fully rich-editable

## Anchor Model

- `document_ref`
- `anchor_id`
- `selector_type` (`line-range`, `offset-range`, `quote`, `block-id`)
- `selector_payload`
- `confidence`

## What Breaks If Edited

- annotation persistence across text changes
- node-to-evidence links
- future document explorer previews

## Acceptance

- a node can attach to one or more text anchors
- anchors survive normal document edits as much as possible
