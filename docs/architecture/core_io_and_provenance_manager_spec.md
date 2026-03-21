# Core I/O and Provenance Manager Spec

## Status

This is an official mixed-status spec.

### Implemented today

- `src/core/io/` exists.
- `WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, and `ProvenanceService` exist in code.
- Adoption is partial; some runtime slices still use inline path I/O.

### Future / target-state

- All runtime nodes should converge on the shared I/O layer.
- Provenance and artifact-writing behavior should become uniform across nodes.

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

Do not mark this spec complete until the components above are adopted consistently by runtime nodes.
