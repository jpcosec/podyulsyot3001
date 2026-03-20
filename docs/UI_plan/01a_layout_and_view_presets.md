# 01a Layout And View Presets

## Goal

Support ordering nodes by meaning, not just by graph topology, and persist named views.

## Status

Partial.

- `dagre` layout exists
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

- keep `dagre` for MVP presets
- add `elkjs` only when compound layouts, multiple handles, or tree/document layouts become hard to manage with `dagre`

## Why Not Jump Straight To `elkjs`

- more power, more tuning cost
- current graph sizes do not yet require it everywhere
- property-based ordering is mostly product logic, not library logic

## What Breaks If Edited

- save/restore flows
- viewport restore expectations
- tree/subflow layouts
- document explorer deep-link views if they rely on stored preset ids

## Acceptance

- user can choose a preset type
- preset can be named and saved
- reloading restores viewport + filters + collapsed state + ordering
