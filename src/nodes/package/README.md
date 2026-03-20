# package Node

This node is the final delivery step in the current prep-match flow.

## What it does now

- reads `nodes/render/approved/state.json`
- verifies hashes for rendered markdown
- writes final markdown files under `final/`
- writes `final/manifest.json`
- marks the run as completed

## Central references

- `docs/graph/nodes_summary.md`
- `docs/graph/node_io_matrix.md`
- `docs/reference/data_management_actual_state.md`
