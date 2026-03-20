# Core I/O and Provenance Manager (Current Status)

## Status

This is now partially implemented and should be treated as a current-state summary, not a "not implemented" placeholder.

Implemented modules under `src/core/io/`:

- `WorkspaceManager`
- `ArtifactReader`
- `ArtifactWriter`
- `ProvenanceService`
- `ObservabilityService` (in `provenance_service.py`)

## What is true today

- The shared I/O layer exists and is used by current runtime nodes such as `review_match`, `render`, `package`, and the prep-match CLI observability writes.
- Path construction, guarded job-relative resolution, atomic writes, JSON/text helpers, and run/node execution snapshots are implemented.
- The current runtime is still mixed: some older nodes continue to do inline file I/O while newer slices use `src/core/io/`.

## What is still incomplete

- The entire node set is not yet migrated to a single uniform I/O pattern.
- Provenance is currently strongest around hashing/render/package/observability, but not every node writes a fully standardized `meta/provenance.json`.
- Some target-state expectations in older docs remain broader than the code that exists today.

## Primary references

- Current code: `src/core/io/`
- Current runtime semantics: `docs/runtime/data_management.md`
- Target-state spec: `plan/spec/core_io_and_provenance_manager_spec.md`
