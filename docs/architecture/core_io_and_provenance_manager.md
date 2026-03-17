# Core I/O and Provenance Manager (Current Status)

Current implementation status: not implemented as a centralized `src/core/io/` layer.

Current behavior in code:

- Nodes still perform inline path construction and direct file reads/writes.
- No shared `WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, or `ProvenanceService` module exists.

Planning/spec details are maintained in:

- `plan/spec/core_io_and_provenance_manager_spec.md`
