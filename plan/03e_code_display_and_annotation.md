# 03e Code Display And Annotation

## Goal

Add code-aware nodes with display, editing, formatting, and annotation hooks.

## Status

Missing.

## Depends On

- `03_rich_content_nodes.md`
- `03a_text_annotation_links.md`

## Candidate Libraries

- `CodeMirror 6` first choice
- `monaco-editor` if IDE-like UX becomes necessary
- `prettier` for formatting

## Recommendation

- use `CodeMirror 6` first because it is lighter and annotation-friendly
- do not bring in Monaco until language services justify the cost

## What Breaks If Edited

- code anchor persistence
- performance on large documents
- bundle size if the editor choice changes late

## Acceptance

- code nodes can render read-only and editable states
- formatting is explicit and safe
- code ranges can be linked to graph nodes
