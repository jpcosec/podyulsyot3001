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

- `@recogito/text-annotator` as the committed text-annotation base
- existing `RichTextPane.tsx` for MVP reuse/adaptation around the chosen anchor model
- `CodeMirror 6` if richer anchor/decorations are needed later
- `Lexical` only if text becomes fully rich-editable

## Anchor Model

- `document_ref`
- `anchor_id`
- `selector_type` (`line-range`, `offset-range`, `quote`, `block-id`)
- `selector_payload`
- `confidence`

## Library Decision

Commit to `Recogito` for text annotations and persistent web-annotation-style anchors.

Required follow-up rules:

- define reattachment strategy after minor text edits
- surface orphaned anchors explicitly when safe reattachment fails
- keep annotation persistence separate from graph node payloads

## What Breaks If Edited

- annotation persistence across text changes
- node-to-evidence links
- future document explorer previews

## Acceptance

- a node can attach to one or more text anchors
- anchors survive normal document edits as much as possible
- the implementation plan assumes `Recogito`, not a custom anchor engine
