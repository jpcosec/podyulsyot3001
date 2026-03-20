# 01a Layout And View Presets

## Goal

Support ordering nodes by meaning, not just by graph topology, and persist named views.

## Status

Partial.

- ad hoc layout exists
- focus-centered layout exists
- manual custom positions can be restored locally
- there are no named presets or property-driven ordering modes

## Depends On

- `01_graph_foundations.md`

## Enables

- `02_structured_documents_and_subflows.md`
- `04a_document_explorer.md`

## Target Preset Types

- `dag_default`
- `focus_centered`
- `timeline_horizontal(property)`
- `compare_lanes_vertical(left_property, right_property)`
- `tree_top_down(root_rule)`
- `manual_saved(name)`

## Data Contract

Each saved view preset should store:

- `preset_id`
- `preset_type`
- `label`
- `parameters`
- `positions` for manual presets only
- `viewport`
- `collapsed_state`
- `filter_state`

## Candidate Libraries

- commit to `elkjs` from the start
- run layout in a worker where practical
- define a benchmark gate before container-heavy defaults or very large graphs become part of the main workflow

## Benchmark Gate

Before treating nested/container-heavy layouts as stable, measure:

- 1000 nodes
- 20 nested containers
- representative edge density for the editor

Success target:

- layout stays interactive enough for explicit user-triggered relayout
- no main-thread lock severe enough to break editing UX

## What Breaks If Edited

- save/restore flows
- viewport restore expectations
- tree/subflow layouts
- document explorer deep-link views if they rely on stored preset ids

## Acceptance

- user can choose a preset type
- preset can be named and saved
- reloading restores viewport + filters + collapsed state + ordering
- `elkjs` is the only committed layout engine in the plan
