# 03c JSON YAML Views

## Goal

Add inspectable and optionally editable structured data nodes.

## Status

Missing.

## Depends On

- `03_rich_content_nodes.md`

## Candidate Libraries

- JSON view: `@uiw/react-json-view`
- lightweight inspect view: `react-inspector`
- editable JSON/YAML: `CodeMirror 6`
- advanced YAML validation: `monaco-yaml` only if needed

## What Breaks If Edited

- schema-linked payload inspection
- datasource inspector panels

## Acceptance

- structured payload nodes can render collapsed and expanded views
- YAML/JSON editing, if enabled, validates before save
