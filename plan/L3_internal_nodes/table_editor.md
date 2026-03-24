# 03d Table Editor

## Goal

Support tabular nodes and structured table editing.

## Status

Missing.

## Depends On

- `03_rich_content_nodes.md`

## Candidate Libraries

- `TanStack Table` for controlled lightweight implementation
- `AG Grid` only if spreadsheet-grade features become required

## Recommendation

- start with read/edit table blocks, not spreadsheet parity

## What Breaks If Edited

- any document node that embeds tabular data
- export/render formatting if tables are used in downstream docs

## Acceptance

- table nodes support row/column editing and typed cell values
