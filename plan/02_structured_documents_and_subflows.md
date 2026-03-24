# 02 Structured Documents And Subflows

## Goal

Use structured graph/subflow patterns for documents, sections, containers, and nested content.

## Status

Partial.

- CV editor already implements group/container ideas close to subflows
- generic node editor does not yet share that model

## Depends On

- `01_graph_foundations.md`
- `01a_layout_and_view_presets.md`
- `01b_node_type_registry_and_modes.md`

## Enables

- `02a_tree_mode_and_outline_sync.md`
- structured document editing
- document-aware layouts

## Proposed Model

- document
  - section
    - block
      - inline anchor / reference node

Each container should support:

- collapsed summary
- expanded content view
- child ordering
- layout strategy
- proxy edges when collapsed

## React Flow Sub-Flows Fit

Strong fit.

- parent/child graph structure already matches the structured-document need
- good for sections, subsections, grouped evidence, grouped references
- should be used as a core document modeling strategy, not only a visual trick

## Candidate Libraries

- React Flow built-in subflow/grouping first
- `elkjs` later if nested layouts become difficult

## What Breaks If Edited

- CV graph editor grouping
- any future outline/document explorer sync
- saved view presets if they reference collapsed state

## Acceptance

- generic editor and CV editor can both represent nested document structures
- collapsed containers preserve context and edge traceability
