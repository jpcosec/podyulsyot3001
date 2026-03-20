# 01b Node Type Registry And Modes

## Goal

Introduce a typed node-type system and extension lifecycle so all future node widgets share a stable contract without growing a large custom registry framework.

## Status

Partial.

- custom node components exist
- focus/edit/minimized behavior exists in fragments
- there is no unified node-type registry

## Depends On

- `01_graph_foundations.md`

## Enables

- `03_rich_content_nodes.md`
- `02_structured_documents_and_subflows.md`

## Registry Shape

Each node type should define:

- `type_id`
- `icon`
- `category`
- `payload_schema`
- `renderers`
  - `minimized`
  - `focus`
  - `edit_in_context`
  - `full_editor`
- `supported_anchors`
- `default_size`
- `allowed_relations`

## Extension Model Decision

- use `Tapable` from the start for extension lifecycle hooks
- keep built-in node features as first-party taps on the same hook surface
- do not introduce `InversifyJS` or a general IoC container
- keep custom code limited to typed lookup tables and adapter glue around Tapable hooks

Expected hook families:

- `onSchemaLoad`
- `onRegistryCompile`
- `onNodeFocus`
- `onModeChange`
- `onInspectorBuild`
- `onContextActionsResolve`

## Initial Node Families

- entity / concept
- structured document block
- markdown document block
- text anchor node
- code block node
- json/yaml payload node
- table node
- image/screenshot node
- datasource/schema node

## React Flow UI Relevance

Useful patterns from React Flow UI:

- base node
- appendix
- tooltip
- database schema node
- labeled group node

These should be treated as implementation templates, not the architecture.

## What Breaks If Edited

- any custom node renderer
- mode switching logic
- persistence if payload schemas change
- explorer icons and grouping if they rely on `type_id`

## Acceptance

- all nodes are rendered through a registry lookup
- each node type supports at least minimized + focus + editor contracts
- icons and affordances are consistent across the app
- extension lifecycle is powered by `Tapable`, not a large custom registry implementation
