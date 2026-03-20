# render Node

This node is the current render stage in the runnable prep-match flow.

## What it does now

- reads generated markdown from `nodes/generate_documents/proposed/`
- copies it into `nodes/render/proposed/`
- writes `nodes/render/approved/state.json` with refs and hashes

## What it does not do yet

- it is not the final PDF/DOCX renderer for the full target architecture
- in the current runnable flow, it is a deterministic markdown render handoff stage

## Central references

- `docs/runtime/node_io_matrix.md`
- `docs/runtime/data_management.md`
