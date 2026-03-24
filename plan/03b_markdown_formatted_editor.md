# 03b Markdown Formatted Editor

## Goal

Upgrade markdown editing from raw textarea to formatted editing and preview.

## Status

Partial.

- plain markdown-ish textarea exists
- no formatted editing view exists

## Depends On

- `03_rich_content_nodes.md`

## Candidate Libraries

- `Lexical` if we want React-first extensibility
- `@tiptap/react` if we want a mature plugin ecosystem quickly
- `Milkdown` if markdown-native authoring becomes central

## Recommendation

- start with split source/rendered preview
- only move to WYSIWYG after deciding markdown round-trip rules

## What Breaks If Edited

- any document node payload shape
- export/render pipeline if formatting introduces unsupported constructs

## Acceptance

- user can switch between raw and formatted views
- markdown stays the source of truth unless explicitly changed later
