# 03f Image Annotation

## Goal

Support screenshot/image nodes with selectable regions that can be linked to graph entities.

## Status

Missing.

## Depends On

- `03_rich_content_nodes.md`

## Candidate Libraries

- `Annotorious`
- `react-image-annotate`

## Recommendation

- start with rectangle regions
- persist region anchors independently of node view state

## Region Anchor Contract

- `image_ref`
- `region_id`
- `shape_type`
- `geometry`
- `label`
- `linked_node_ids`

## What Breaks If Edited

- image anchor persistence
- document explorer thumbnails/previews

## Acceptance

- users can create, edit, and link image regions to graph nodes
