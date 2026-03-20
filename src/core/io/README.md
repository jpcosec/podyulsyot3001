# Core I/O Layer

This directory contains the shared job-workspace I/O layer currently used by newer runtime slices.

## Components

- `workspace_manager.py` - safe workspace and artifact path resolution
- `artifact_reader.py` - text/JSON read helpers
- `artifact_writer.py` - atomic text/JSON writes
- `provenance_service.py` - hashing and observability helpers

## Current reality

- this layer exists and is used by `review_match`, `render`, `package`, and run summaries
- migration is still partial; some older nodes still do inline file I/O

## Central references

- `docs/architecture/core_io_and_provenance_manager.md`
- `docs/reference/data_management_actual_state.md`
