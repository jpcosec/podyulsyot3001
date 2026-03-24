# 03 Rich Content Nodes

## Goal

Move from plain attribute bags to typed rich content nodes.

## Status

Missing as a system.

## Depends On

- `01b_node_type_registry_and_modes.md`
- `01c_editor_state_and_history_contract.md`

## Enables

- `03a_text_annotation_links.md`
- `03b_markdown_formatted_editor.md`
- `03c_json_yaml_views.md`
- `03d_table_editor.md`
- `03e_code_display_and_annotation.md`
- `03f_image_annotation.md`

## Core Principle

Rich content should be attached through typed payloads and references, not improvised HTML blobs.

## Shared Rich Node Contract

- `content_type`
- `payload`
- `display_mode`
- `anchor_refs`
- `external_asset_refs`
- `edit_capabilities`

## What Breaks If Edited

- persistence compatibility across node types
- rendering contracts
- annotation attachment model

## Acceptance

- all future rich nodes can plug into one shared contract
