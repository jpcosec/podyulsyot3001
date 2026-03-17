# Core I/O and Provenance Manager Spec

Status: planned, not implemented.

## Intended location

- `src/core/io/`

## Planned components

1. `WorkspaceManager`
2. `ArtifactReader`
3. `ArtifactWriter`
4. `ProvenanceService`

## Purpose

Centralize data-plane path resolution and read/write/provenance behavior so node logic stays deterministic and free of inline path construction.

## Implementation gate

Do not mark this spec complete until the components above exist in code and are used by newly implemented nodes.
