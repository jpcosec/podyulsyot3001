# package Node

This node is the final delivery step in the current prep-match flow.

## What it does now

- reads `nodes/render/approved/state.json`
- verifies hashes for rendered markdown
- writes final markdown files under `final/`
- writes `final/manifest.json`
- marks the run as completed

## Central references

- `docs/runtime/graph_flow.md`
- `docs/runtime/node_io_matrix.md`
- `docs/runtime/data_management.md`
