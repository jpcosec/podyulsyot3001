# generate_documents_v2: assembly dual-write is temporary bridge code

**Why deferred:** Removing it requires updating the render pipeline to read from `generate_documents_v2` paths — a coordinated change planned for the generate-documents cut-over (Plan 3).
**Last reviewed:** 2026-03-31

## Problem

`_persist_render_inputs` in `src/core/ai/generate_documents_v2/nodes/assembly.py` (lines 105–128) writes each markdown file to **two** node directories:

```python
for node_name in ("generate_documents_v2", "generate_documents"):
    for filename, content in files.items():
        data_manager.write_text_artifact(node_name=node_name, ...)
```

The canonical v2 output lands at `nodes/generate_documents_v2/proposed/`. The duplicate copy lands at `nodes/generate_documents/proposed/`. The three render-pipeline ref keys (`cv_markdown_ref`, `letter_markdown_ref`, `email_markdown_ref`) are intentionally pointed at the **old** path so that `src/graph/nodes/render.py` finds them without modification.

This was necessary because `src/graph/nodes/render.py` was built against the original `generate_documents/` module path and has not been updated yet.

## Why It Matters

- Two copies of every output file are written to disk on every run (6 markdown files × 2 = 12 writes).
- If a consumer reads the v2 path directly (e.g. standalone graph runs), they get correct output. If a consumer reads the `generate_documents` path, they get the bridge copy — and both are identical, so the inconsistency is invisible until paths diverge.
- If the dual-write is removed before `render.py` is updated, `cv_markdown_ref` and `letter_markdown_ref` will be missing from `artifact_refs` and the render node will silently skip rendering both documents.

## Proposed Direction (Plan 3 cut-over)

1. Update `src/graph/nodes/render.py` to read from `generate_documents_v2` node paths.
2. Update ref keys to point at v2 paths: `cv_markdown_ref`, `letter_markdown_ref`, `email_markdown_ref`.
3. Remove the `"generate_documents"` iteration from `_persist_render_inputs`, leaving only `"generate_documents_v2"`.
4. Delete or repurpose the old `generate_documents/` node path convention.

## Linked TODOs

- `src/core/ai/generate_documents_v2/nodes/assembly.py:105` — `# TODO(future): dual-write is a bridge until render.py reads from generate_documents_v2 — see future_docs/issues/generate_documents_v2_assembly_dual_write.md`
