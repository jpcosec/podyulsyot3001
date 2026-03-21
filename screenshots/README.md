# Screenshots Inventory

This folder contains product and sandbox screenshots of the UI currently implemented in the local review workbench.

## Notes

- These screenshots were captured against the local UI stack.
- Product screenshots use the sample job `tu_berlin/999001`.
- They are intended for UI/UX discussion, product walkthroughs, and design handoff.
- Product surfaces and sandbox surfaces are separated intentionally.

## Product / operator surfaces

### `01-portfolio-dashboard.png`

- Route: `/`
- Shows the main dashboard.
- Includes top-level stats, review queue hints, job list, and links to current workstreams.

### `02-job-workspace-overview.png`

- Route: `/jobs/tu_berlin/999001`
- Shows the per-job workspace shell.
- Includes breadcrumbs, current node, stage timeline, and the main review tabs.

### `03-job-view1-graph-explorer.png`

- Route: `/jobs/tu_berlin/999001?view=view-1`
- Shows View 1 Graph Explorer.
- Focuses on match graph relationships and match table summaries.

### `04-job-view2-document-to-graph.png`

- Route: `/jobs/tu_berlin/999001?view=view-2`
- Shows View 2 Document to Graph.
- Focuses on source text lines, requirement selection, and requirement-linked graph context.

### `05-job-view3-graph-to-document.png`

- Route: `/jobs/tu_berlin/999001?view=view-3`
- Shows View 3 Graph to Document.
- Focuses on generated documents and the contributing graph context.

### `06-job-pipeline-outputs-extract.png`

- Route: `/jobs/tu_berlin/999001?view=outputs&stage=extract_understand`
- Shows Pipeline Outputs for `extract_understand`.
- Focuses on local JSON artifact inspection/editing for extraction output.

### `07-job-pipeline-outputs-match.png`

- Route: `/jobs/tu_berlin/999001?view=outputs&stage=match`
- Shows Pipeline Outputs for `match`.
- Focuses on local JSON artifact inspection/editing for match output.

### `08-job-pipeline-outputs-documents.png`

- Route: `/jobs/tu_berlin/999001?view=outputs&stage=generate_documents&file=nodes/generate_documents/proposed/motivation_letter.md`
- Shows Pipeline Outputs for `generate_documents` with a document selected.
- Focuses on markdown document editing directly on local artifacts.

### `09-job-pipeline-outputs-scrape-diagnostics.png`

- Route: `/jobs/tu_berlin/999001?view=outputs&stage=scrape&file=nodes/scrape/trace/error_screenshot.png`
- Shows Pipeline Outputs for `scrape` with the diagnostic screenshot selected.
- Focuses on scrape troubleshooting, artifacts, and screenshot evidence.

### `10-job-node-editor-extract.png`

- Route: `/jobs/tu_berlin/999001/node-editor?stage=extract_understand`
- Shows the local JSON-backed node editor in extract mode.
- Focuses on graph-shaped editing of extraction state.

### `11-job-node-editor-match.png`

- Route: `/jobs/tu_berlin/999001/node-editor?stage=match`
- Shows the local JSON-backed node editor in match mode.
- Focuses on requirement -> match -> evidence graph editing.

## Sandbox / prototype surfaces

### `12-sandbox-index.png`

- Route: `/sandbox`
- Shows the sandbox landing page.
- Used as an entry point for experimental UI surfaces.

### `13-sandbox-node-editor-fullscreen.png`

- Route: `/sandbox/node_editor`
- Shows the fullscreen Node Editor sandbox.
- This is the most advanced graph interaction prototype currently in the repo.

### `14-sandbox-cv-graph.png`

- Route: `/sandbox/cv_graph`
- Shows the CV Graph editor sandbox.
- Focuses on profile knowledge graph editing concepts.

### `15-sandbox-text-tagger.png`

- Route: `/sandbox/text_tagger`
- Shows the Text Tagger sandbox.
- Focuses on text annotation and tagging interaction patterns.

## Recommended use in design discussions

If the goal is product design, start with:

1. `01-portfolio-dashboard.png`
2. `02-job-workspace-overview.png`
3. `04-job-view2-document-to-graph.png`
4. `06-job-pipeline-outputs-extract.png`
5. `07-job-pipeline-outputs-match.png`
6. `08-job-pipeline-outputs-documents.png`
7. `09-job-pipeline-outputs-scrape-diagnostics.png`
8. `13-sandbox-node-editor-fullscreen.png`

That set covers the most relevant current and near-future UX surfaces.
