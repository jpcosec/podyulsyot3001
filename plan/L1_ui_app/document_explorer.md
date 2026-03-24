# 04a Document Explorer

## Goal

Provide a unified explorer for jobs, documents, schemas, datasource objects, and graph-linked assets.

## Status

Partial.

- job and stage browsing exists
- there is no unified explorer surface

## Depends On

- `01a_layout_and_view_presets.md`
- `04_external_data_and_schema_integration.md`

## Candidate Libraries

- `react-arborist`
- `TanStack Virtual` if explorer size grows large

## Explorer Sections

- jobs
- documents
- graph views / saved presets
- schemas
- datasource objects
- media assets

## What Breaks If Edited

- deep linking to graph views
- selection sync with graph and document panes

## Acceptance

- explorer selection can drive graph focus and document preview
- explorer can expose saved graph/document views
