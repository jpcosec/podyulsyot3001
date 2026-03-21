# Review Workbench Product Brief

## 1. Product Summary

PhD 2.0 is a local-first review and generation system for PhD job applications.

Its purpose is to turn a scraped job posting plus candidate profile evidence into reviewed application artifacts:

1. structured extraction of the posting
2. requirement-to-evidence matching
3. generated application documents
4. human review checkpoints before semantic acceptance

The current product direction is **minimal viable architecture**:

- no Neo4j as the working data format
- no heavy enterprise orchestration in the UI
- all operational truth lives in local job folders under `data/jobs/<source>/<job_id>/`
- the UI is a review and correction surface over those real artifacts

This brief is for designing the operator-facing UI/UX of the current product, not the long-term speculative graph platform.

## 2. Product Goals

### Primary goals

1. Make every important pipeline stage inspectable by a human.
2. Let the operator correct structured outputs without editing raw files by hand.
3. Preserve auditability: every UI action should map back to local artifacts.
4. Keep the system local-first and deterministic where possible.

### Secondary goals

1. Reduce the need to jump between CLI, filesystem, and browser.
2. Make scraping failures diagnosable through visible evidence.
3. Support future richer graph UIs without changing the local JSON source of truth.

## 3. Core Product Logic

The current runnable flow is:

`scrape -> translate_if_needed -> extract_understand -> match -> review_match -> generate_documents -> render -> package`

### Logical meaning of each stage

1. `scrape`
   - fetch the job posting
   - preserve raw snapshot, fetch metadata, extraction output, canonical scrape
   - if scraping fails in browser mode, save visual evidence

2. `translate_if_needed`
   - translate job text into a normalized working language when necessary

3. `extract_understand`
   - turn source text into structured job understanding
   - examples: title, requirements, constraints, risks, contact info, optional salary grade

4. `match`
   - map job requirements to candidate evidence
   - attach scores and reasoning

5. `review_match`
   - human checkpoint for semantic approval or regeneration

6. `generate_documents`
   - produce CV delta, motivation letter, and application email drafts

7. `render`
   - convert approved text outputs into final render artifacts

8. `package`
   - produce final deliverable set for the application

### Human-in-the-loop logic

The product is not supposed to silently trust the model. The UI exists because semantic outputs need human review and correction.

The intended operator loop is:

1. inspect current stage outputs
2. compare structured result with source evidence
3. correct structured data or generated text
4. save back to local artifacts
5. continue pipeline execution or resume from CLI

## 4. Source of Truth and Data Model Philosophy

### Current source of truth

All data is local and file-based.

Primary location:

- `data/jobs/<source>/<job_id>/`

Key artifact conventions:

- `nodes/<node>/approved/state.json`
- `nodes/<node>/proposed/*.md`
- `nodes/<node>/review/decision.md`
- `nodes/<node>/trace/error_screenshot.png`
- `raw/source_text.md`

### Important product constraint

The UI is not the source of truth.

The UI is a projection/editor over disk artifacts.

That means the designer should assume:

1. save actions write back to local files
2. stage views are artifact-centric
3. data may be incomplete or missing for some stages
4. every screen should degrade gracefully when an artifact does not exist yet

## 5. Target User

Current primary user:

- a technical operator / researcher applying to PhD positions

They are comfortable with:

- running local commands
- reviewing structured information critically
- editing machine-produced drafts

They do **not** want to:

- manually hunt for files in folders
- debug scraping blind
- guess which pipeline stage failed
- rewrite everything in raw JSON unless necessary

## 6. Current Stack

## Frontend

- React 18
- TypeScript
- Vite
- React Router
- `@xyflow/react` for graph editing / node editing surfaces
- Tailwind v4 available in the app stack, but the current styling is mostly app-specific CSS in `apps/review-workbench/src/styles.css`
- additional sandbox/editor dependencies:
  - `@dagrejs/dagre`
  - `dagre`
  - `@dnd-kit/core`
  - `@dnd-kit/utilities`
  - `slate`
  - `slate-react`

## Backend

- FastAPI
- Pydantic
- local filesystem I/O through project services
- no DB required for the current minimal architecture

## AI layer

- Gemini model usage
- LangChain wrappers are being introduced for structured output
- LangSmith is intended for tracing/auditability of LLM stages
- LangGraph orchestration remains the pipeline orchestrator in code

## Operational mode

- local-first
- JSON-first
- file-backed review and editing

## 7. Current UI Surfaces

This section separates **operator surfaces** from **sandbox/prototype surfaces**.

## 7.1 Operator surfaces

### A. Portfolio Page

Route:

- `/`

Purpose:

- landing page for the review workbench
- overview of jobs and statuses
- quick access to workstreams and operator commands

What it currently shows:

1. high-level job counters
2. job tree / job list
3. review queue hint
4. links to sandbox workstreams
5. operator quick commands

UX role:

- command center / dashboard

Design need:

- it currently mixes product UI and developer dashboard concerns
- needs a clearer split between operator work and experimental tooling

### B. Job Workspace Page

Route:

- `/jobs/:source/:jobId`

Purpose:

- main per-job workspace
- timeline overview + stage switching + review entry point

What it currently shows:

1. breadcrumbs
2. job identity
3. current node / current stage
4. stage list with statuses
5. tabbed views
   - View 1 Graph Explorer
   - View 2 Document to Graph
   - View 3 Graph to Document
   - Pipeline Outputs
6. link to the local job node editor

UX role:

- central navigation shell for a single job

Design need:

- should become the main operational hub for stage-based review
- needs stronger information architecture and clearer action hierarchy

### C. Pipeline Outputs View

Embedded in job workspace.

Purpose:

- inspect real local artifacts for the currently selected stage
- edit structured JSON or markdown where allowed
- preview scrape screenshots

What it currently supports:

1. stage-based artifact list
2. JSON preview
3. markdown preview/edit
4. screenshot preview for scrape failures
5. save-to-file behavior for:
   - `extract_understand`
   - `match`
   - generated documents

UX role:

- raw artifact inspector / fallback editor / stage debugger

Design need:

- important operational surface
- should feel like a deliberate inspector, not a developer dump

### D. Job Node Editor Page

Route:

- `/jobs/:source/:jobId/node-editor`

Purpose:

- graph-shaped editor over local JSON for the two most important structured stages
  - `extract_understand`
  - `match`

What it currently does:

1. load the JSON state for the selected stage
2. build a lightweight graph projection
3. let the user click a node/object path
4. edit the selected JSON fragment
5. save back to `state.json`

UX role:

- minimal structured editor over local artifacts

Design need:

- this should evolve toward reusing the full `NodeEditor` interaction language rather than staying as a plain JSON+graph helper

### E. View 1 - Graph Explorer

Purpose:

- show graph relationships in the matching space
- especially requirement -> match -> evidence understanding

Current behavior:

1. graph display
2. match table with score and reasoning

UX role:

- read-only semantic overview of matching

### F. View 2 - Document to Graph

Purpose:

- compare extracted requirements against source text
- navigate from text to structured requirements

Current behavior:

1. source text displayed line by line
2. extracted requirements list
3. requirement-linked spans
4. graph view of source -> requirement links

UX role:

- extraction review surface

Important logic:

- this view is central to the deterministic evidence-linking concept
- the product should not rely on invented offsets from the LLM

### G. View 3 - Graph to Document

Purpose:

- inspect generated documents in relation to their source graph context

Current behavior:

1. tabbed documents
   - motivation letter
   - CV
   - email
2. contributing graph nodes view

UX role:

- text generation review surface

## 7.2 Sandbox / prototype surfaces

These are important for design direction, but they are not the main operator product yet.

### Sandbox Index

Route:

- `/sandbox`

Purpose:

- launcher for experimental interaction surfaces

### Node Editor Sandbox

Route:

- `/sandbox/node_editor`

Purpose:

- advanced graph editing behavior prototype

Capabilities already explored there:

1. focus mode
2. filter modes
3. relation editing
4. node editing
5. connect flows
6. layout controls
7. action history
8. copy/paste
9. delete flows
10. floating workspace behaviors

This is strategically important because the product should **reuse this interaction language** rather than invent a second, unrelated graph editor.

### CV Graph Editor Sandbox

Route:

- `/sandbox/cv_graph`

Purpose:

- prototype for profile knowledge graph editing

### Text Tagger Sandbox

Route:

- `/sandbox/text_tagger`

Purpose:

- prototype for text annotation and tagging workflows

## 8. Product-Level Functionalities

### Already present in the product

1. portfolio summary and job listing
2. job timeline and stage visibility
3. stage-based review navigation
4. graph exploration for matching
5. source-to-requirement review
6. generated document inspection
7. local JSON state editing for extraction and matching
8. local markdown editing for generated documents
9. scrape artifact inspection including screenshots

### Product-critical behaviors

1. all edits must persist to local artifacts
2. missing stage outputs should not crash the UI
3. the operator should always know what stage they are looking at
4. the operator should be able to move between source text, structured graph, and generated documents

## 9. Product Logic the Designer Must Understand

### A. This is not a generic graph app

The graph is not decorative. It is a human-review representation of machine-generated application logic.

There are three semantic spaces:

1. source document understanding
2. requirement-to-evidence matching
3. graph-to-document grounding

The UI should help the user move between those spaces.

### B. Human review is mandatory, not optional

This product assumes model output is useful but not final.

Therefore the UX should support:

1. inspection
2. correction
3. confidence building
4. provenance visibility

### C. Local artifact visibility is a feature, not a hack

Being able to see:

- the source text
- the extracted state
- the match state
- generated markdown
- scrape screenshots

is part of the product value because it keeps the system auditable.

### D. Deterministic evidence linking matters

The designer should assume the product wants a reliable link between source text and structured evidence.

Important principle:

- the system should not invent text coordinates
- it should link evidence by matching real text fragments in the stored source text

In design terms, this means the UI needs room for:

1. source text highlighting
2. evidence snippets
3. visible grounding relationships
4. graceful handling when a quote cannot be resolved

## 10. Current API Surface Relevant to UX

### Portfolio

- `GET /api/v1/portfolio/summary`

### Job workspace

- `GET /api/v1/jobs/{source}/{job_id}/timeline`
- `GET /api/v1/jobs/{source}/{job_id}/view1`
- `GET /api/v1/jobs/{source}/{job_id}/view2`
- `GET /api/v1/jobs/{source}/{job_id}/view3`
- `GET /api/v1/jobs/{source}/{job_id}/review/match`

### Local artifact editing

- `GET /api/v1/jobs/{source}/{job_id}/editor/{node_name}/state`
- `PUT /api/v1/jobs/{source}/{job_id}/editor/{node_name}/state`
- `GET /api/v1/jobs/{source}/{job_id}/stage/{stage}/outputs`
- `GET /api/v1/jobs/{source}/{job_id}/documents/{doc_key}`
- `PUT /api/v1/jobs/{source}/{job_id}/documents/{doc_key}`

## 11. Key UX Problems to Solve

1. The current job workspace still feels like a set of technical views, not one coherent operator workflow.
2. The portfolio page is half dashboard, half developer launcher.
3. The node editor experience is split between a powerful sandbox and a simpler per-job editor.
4. Document review is functional but not yet polished as a real editorial experience.
5. Scrape diagnostics exist, but they need a clearer operator-facing presentation.

## 12. UX Opportunities

### Opportunity 1: One coherent per-job review workspace

The ideal near-term UI is a single job workspace where the operator can:

1. see where the pipeline is
2. inspect artifacts for the current stage
3. edit the relevant structure or text
4. move to the next review task without context switching

### Opportunity 2: Reuse the Node Editor language everywhere it makes sense

Instead of building separate micro-editors for each stage, the product should converge on a shared interaction language:

1. select node
2. inspect connected relations
3. edit fields in context
4. save to local artifacts

### Opportunity 3: Treat provenance as part of the visual language

The UI should communicate:

1. where this information came from
2. what stage produced it
3. whether it is proposed, approved, reviewed, or failed

## 13. Desired Deliverables from a UI/UX Designer

We would ideally want:

1. information architecture for the operator product
2. view inventory with purpose and transitions
3. wireframes for the job workspace
4. wireframes for the extraction review experience
5. wireframes for the matching review experience
6. wireframes for document editing / redaction review
7. a proposal for how the existing sandbox `NodeEditor` becomes the product editor
8. a clear separation between:
   - operator UI
   - sandbox/prototyping UI
   - future/non-priority surfaces

## 14. What Not to Optimize For Yet

1. multi-user collaboration
2. cloud deployment assumptions
3. Neo4j-native data exploration
4. large-scale graph analytics
5. abstract enterprise dashboards

## 15. Design Constraints

1. Must work well on desktop first.
2. Should still load and remain usable on smaller screens.
3. Must tolerate incomplete data.
4. Must preserve the mental model of local artifact-backed review.
5. Should not require the user to understand internal code structures.
6. Should be compatible with future richer graph editing, not block it.

## 16. One-Sentence Product Definition

PhD 2.0 Review Workbench is a local-first human review interface for inspecting, correcting, and approving the structured and textual outputs of an AI-assisted PhD application pipeline, directly on top of real job artifacts stored on disk.
