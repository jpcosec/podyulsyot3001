# 00 Status Matrix

## Goal

Provide a compact map of requested UI capabilities: done, partial, missing, and what they depend on.

## Current Status

| Capability | Status | Current base | Main gap | Depends on |
|---|---|---|---|---|
| Property-based ordering | Partial | `NodeEditorSandboxPage.tsx` layout functions | no layout presets or property mappers | `01_graph_foundations`, `01a_layout_and_view_presets` |
| Save custom orderings | Partial | local sandbox snapshot, CV graph API save | no named persistent view presets | `01a_layout_and_view_presets`, `04_external_data_and_schema_integration` |
| Trees | Partial | CV graph group/container model | not generalized across editor | `02_structured_documents_and_subflows` |
| Custom HTML components in nodes | Partial | custom React Flow nodes | no node-type registry | `01b_node_type_registry_and_modes` |
| Image annotation | Missing | none | no media node / anchor model | `03_rich_content_nodes`, `03f_image_annotation` |
| Text tagger linked to nodes | Partial | `RichTextPane.tsx`, View 2 links | not generalized as graph anchor model | `03a_text_annotation_links` |
| Code display/editor | Missing | none | no code node, no anchor persistence | `03e_code_display_and_annotation` |
| JSON/YAML views | Missing | none | no structured payload renderer | `03c_json_yaml_views` |
| Table editor | Missing | none | no grid model | `03d_table_editor` |
| Formatted markdown editing | Partial | plain textarea only | no rich/formatted editor | `03b_markdown_formatted_editor` |
| Sub-flows for documents | Partial | CV group/child graph | no shared structured-doc graph model | `02_structured_documents_and_subflows` |
| Node type icons / modes | Partial | categories, focus/edit states | no shared type registry / icon system | `01b_node_type_registry_and_modes` |
| External datasource/schema/neo4j structure | Partial | REST API + docs | no explicit UI architecture | `04_external_data_and_schema_integration` |
| Document explorer | Partial | job list + pages | no unified explorer | `04a_document_explorer` |

## Existing Strong Reuse Points

- graph canvas and interaction shell: `NodeEditorSandboxPage.tsx`
- structured grouping and collapsed proxy edges: `CvGraphEditorPage.tsx`
- text span annotation: `RichTextPane.tsx`
- persisted graph API shape: `src/interfaces/api/routers/portfolio.py`

## High-Risk Areas

- node content types before registry stabilization
- external data integration before defining persistence boundaries
- image/code annotation before defining anchor identity rules

## Immediate Recommendation

Implement foundations first, not widgets first.

- define node types
- define layout/view presets
- define editor persistence boundary
- then add richer node payloads
