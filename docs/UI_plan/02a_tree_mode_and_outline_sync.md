# 02a Tree Mode And Outline Sync

## Goal

Provide a tree/outline view synchronized with graph structure.

## Status

Missing as a shared feature.

## Depends On

- `02_structured_documents_and_subflows.md`
- `04a_document_explorer.md`

## Candidate Libraries

- `react-arborist` as the primary tree/explorer library
- `d3-hierarchy` only if a dedicated tree layout algorithm is needed inside canvas

## Responsibilities

- reflect nested graph hierarchy
- support selection sync
- support expand/collapse sync
- support drag reorder where valid

## What Breaks If Edited

- subflow structure integrity
- explorer navigation expectations
- saved outline expansion state

## Acceptance

- selecting a tree item focuses the graph node
- expanding/collapsing works from both tree and graph
