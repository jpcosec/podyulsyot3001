# UI Plan

This folder treats UI development as a dependency graph rather than a flat backlog.

Each file is a graph node with:

- scope
- current status
- dependencies
- enables
- what breaks if edited
- candidate libraries
- acceptance notes

## Current Context

- Main generic graph sandbox: `apps/review-workbench/src/sandbox/pages/NodeEditorSandboxPage.tsx`
- Structured graph/editor baseline: `apps/review-workbench/src/sandbox/pages/CvGraphEditorPage.tsx`
- Text tagging baseline: `apps/review-workbench/src/sandbox/components/RichTextPane.tsx`
- UI behavior docs: `docs/architecture/node_editor_behavior_spec.md`

## React Flow UI Notes

Reference checked: `https://reactflow.dev/ui`

- React Flow UI provides copyable components, not a black-box package.
- It is designed around `shadcn/ui` + Tailwind.
- Good candidates for reuse here:
  - base node patterns
  - labeled group node patterns
  - database schema node patterns
  - button/data edges
  - node search / zoom controls
- Recommendation: borrow patterns selectively, do not adopt wholesale before defining our node-type registry.

## Graph Overview

```text
00_status_matrix
  -> 01_graph_foundations
  -> 04_external_data_and_schema_integration

01_graph_foundations
  -> 01a_layout_and_view_presets
  -> 01b_node_type_registry_and_modes
  -> 01c_editor_state_and_history_contract

01a_layout_and_view_presets
  -> 02_structured_documents_and_subflows
  -> 04a_document_explorer

01b_node_type_registry_and_modes
  -> 03_rich_content_nodes
  -> 02_structured_documents_and_subflows

01c_editor_state_and_history_contract
  -> 03_rich_content_nodes
  -> 04_external_data_and_schema_integration

02_structured_documents_and_subflows
  -> 02a_tree_mode_and_outline_sync

03_rich_content_nodes
  -> 03a_text_annotation_links
  -> 03b_markdown_formatted_editor
  -> 03c_json_yaml_views
  -> 03d_table_editor
  -> 03e_code_display_and_annotation
  -> 03f_image_annotation

04_external_data_and_schema_integration
  -> 04a_document_explorer
  -> 05_validation_and_test_impact_map

All nodes
  -> AGENT_REVIEWER_ENTRYPOINT
```

## Recommended Build Order

1. `00_status_matrix.md`
2. `01_graph_foundations.md`
3. `01a_layout_and_view_presets.md`
4. `01b_node_type_registry_and_modes.md`
5. `01c_editor_state_and_history_contract.md`
6. `02_structured_documents_and_subflows.md`
7. `02a_tree_mode_and_outline_sync.md`
8. `03_rich_content_nodes.md`
9. `03a_text_annotation_links.md`
10. `03b_markdown_formatted_editor.md`
11. `03c_json_yaml_views.md`
12. `03d_table_editor.md`
13. `03e_code_display_and_annotation.md`
14. `03f_image_annotation.md`
15. `04_external_data_and_schema_integration.md`
16. `04a_document_explorer.md`
17. `05_validation_and_test_impact_map.md`
18. `AGENT_REVIEWER_ENTRYPOINT.md`

## Library Summary

- layout / compound graphs: `dagre` now, `elkjs` later
- explorer trees: `react-arborist`
- rich text / markdown: `Lexical` or `@tiptap/react`
- code editor: `CodeMirror 6` first, `monaco-editor` only if IDE-grade features are needed
- json tree: `@uiw/react-json-view`
- yaml editor: `CodeMirror 6` + yaml mode or `monaco-yaml`
- tables: `TanStack Table` first, `AG Grid` only if spreadsheet-grade workflows become mandatory
- image annotation: `Annotorious` or `react-image-annotate`

## Planning Rule

Do not implement rich node content or explorer surfaces before stabilizing:

- node type registry
- editor state model
- layout/view preset contract
- persistence boundary
