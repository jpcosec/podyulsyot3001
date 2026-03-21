# UI View Spec — Review Workbench

> Mapping between the UI sample mockups (`plan/01_ui/UI samples/`) and the current React implementation. Target audience: UI/UX designer doing the hand-over pass.

## Visual Design Language (already established)

All samples share the same palette and type system — this is **not** a design direction to decide, it is a constraint to respect:

| Token | Value | Usage |
|---|---|---|
| Background | `#0c0e10` | Page background |
| Surface dim | `#121416` | Secondary surfaces |
| Surface container | `#171a1c` | Cards, panels |
| Surface container high | `#1d2022` | Elevated cards |
| On-surface | `#eeeef0` | Primary text |
| On-surface variant | `#b9cacb` | Secondary text |
| Outline | `#747578` | Borders |
| Primary | `#99f7ff` | Interactive, links |
| Primary fixed | `#00f1fe` | Active states |
| Secondary | `#fecb00` | Highlights, badges |
| Secondary container | `#ffaa00` | Warning chips |
| Tertiary | `#ff7254` | Errors, alerts |
| Error | `#ff716c` | Error states |

- **Typefaces**: Space Grotesk (headings), Inter (body), JetBrains Mono (code, paths, IDs)
- **Icon library**: Material Symbols Outlined
- **Style**: "Terran Command" — dark terminal aesthetic, not a generic SaaS dashboard

## View Inventory

The product has **5 top-level views** (URL routes):

| Route | View name | Implemented | Sample reference |
|---|---|---|---|
| `/` | Portfolio | ✅ | `global_porfolio_view.html` |
| `/jobs/:source/:jobId` | Job workspace | ✅ | `extraction.html` + `matching*.html` |
| `/jobs/:source/:jobId/node-editor` | Node editor | ✅ | partial — see gap below |
| `/jobs/:source/:jobId` outputs tab | Pipeline outputs | ✅ | `document_generation.html` |
| `/jobs/:source/:jobId` outputs tab (scraping) | Scrape diagnostics | ✅ | (not sampled) |
| — | Deployment / package | ❌ | `deployment.html` |

Within `/jobs/:source/:jobId` there are 4 sub-tabs (view-1 through view-3 + outputs), all listed above.

---

## View 1: Graph Explorer

**Route**: `/jobs/:source/:jobId` + view-1 tab
**Current component**: `ViewOneGraphExplorer.tsx`
**Sample reference**: `matching.html` (right panel) + `matching2.html`

### What exists today

- `GraphCanvas` renders match graph nodes + edges (requirement → evidence nodes)
- Edge labels show `MATCHED_BY` + score
- Match reasoning displayed as text rows below graph
- Data loaded via `getViewOnePayload()`

### Gaps vs. sample

| Gap | Description |
|---|---|
| Profile evidence bank panel | Sample has left sidebar listing all profile evidence entries (skills, projects, education) with status chips. Current implementation shows no evidence bank. |
| Match quality indicators | Sample shows color-coded quality (green/amber/red) per match edge. Current shows raw score only. |
| Requirement coverage bar | Sample shows a "coverage" progress indicator per requirement (e.g., "3/5 matched"). Not implemented. |
| Evidence source chips | Sample shows provenance chips per evidence node (e.g., "CV:project:Pub 3"). Not implemented. |
| Edge interactivity | Sample edges are clickable for detailed reasoning. Current edges are display-only. |
| Candidate profile summary | Sample has a compact profile card (photo, name, key stats) at top-left. Not implemented. |

---

## View 2: Document to Graph (Extraction Review)

**Route**: `/jobs/:source/:jobId` + view-2 tab
**Current component**: `ViewTwoDocToGraph.tsx`
**Sample reference**: `extraction.html` + `matching.html` (left panel)

### What exists today

- Source markdown rendered as line-by-line buttons
- Highlighted lines for selected requirement's spans
- Line-level click selects linked requirement
- Requirement panel shows ID, priority, text, spans
- GraphCanvas shows source → requirements topology

### Gaps vs. sample

| Gap | Description |
|---|---|
| Difficulty rating | Sample shows a difficulty indicator (color dot) per requirement extracted from job text. |
| Requirement metadata | Sample shows `type` chip (skill/experience/certification) per requirement. Current shows only ID. |
| Confidence score | Sample shows per-requirement confidence (e.g., 0.87). Current has no confidence display. |
| Evidence linking | Sample's matching panel (right) shows requirement → evidence mapping with score. This is essentially View 1's domain. |
| Edit extraction inline | User cannot edit requirement text from this view — must go to node editor. Sample implies inline edit capability. |
| Batch approve/reject | Sample has bulk selection checkboxes for requirements. Not implemented. |
| Exact quote highlight | Sample highlights the exact character span in the source text, not just line-level. Current uses line-level spans. |

---

## View 3: Graph to Document

**Route**: `/jobs/:source/:jobId` + view-3 tab
**Current component**: `ViewThreeGraphToDoc.tsx`
**Sample reference**: `document_generation.html`

### What exists today

(Need to read the current `ViewThreeGraphToDoc.tsx` — listed in view inventory but content unknown)

### Gaps vs. sample

| Gap | Description |
|---|---|
| Section-level sculpting | Sample has per-section controls (weight, tone, length). Current view may be read-only preview. |
| Contrast diff | Sample shows diff view between proposed and approved document versions. Not implemented. |
| Per-section confidence | Sample shows confidence rating per document section (derived from match score). |
| Insert evidence shortcut | Sample allows inserting evidence snippets into document via button. Not implemented. |
| Character/word count | Sample has live count per section. Not implemented. |
| Version history | Sample shows version timeline sidebar. Not implemented. |

---

## Pipeline Outputs View

**Route**: `/jobs/:source/:jobId` + outputs tab
**Current component**: `PipelineOutputsView.tsx`
**Sample reference**: `document_generation.html` (document editing portion)

### What exists today

- File list for selected stage (JSON, Markdown, PNG)
- Read-only preview for non-editable files
- JSON editor (textarea) for extract_understand and match nodes
- Markdown editor for cv.md, motivation_letter.md, application_email.md
- Save to `nodes/<node>/proposed/state.json` or `proposed/*.md`
- PNG viewer for screenshots (scraping diagnostics)

### Gaps vs. sample

| Gap | Description |
|---|---|
| Syntax-highlighted editor | Current uses raw `<textarea>`. Sample implies a rich editor. |
| Side-by-side diff | No diff view between proposed and approved. |
| Approval workflow | Sample has "Approve section" buttons. Current has save-only. |
| Stage timeline | Sample shows pipeline stage timeline in sidebar. Current shows flat file list. |
| Artifact metadata | Sample shows file size, modified date. Current shows only path. |

---

## Node Editor Page

**Route**: `/jobs/:source/:jobId/node-editor`
**Current component**: `JobNodeEditorPage.tsx`
**Sample reference**: No dedicated sample; this is an internal tool

### What exists today

- ReactFlow graph visualization of extract_understand and match state
- Click node → path selected in sidebar JSON editor
- Save edited JSON back to `state.json`
- Two stage tabs: Extract and Match
- JSON path navigation with dot-notation

### Gaps vs. sample

| Gap | Description |
|---|---|
| Visual node type differentiation | Sample nodes have type-specific colors (requirement, constraint, risk). Current uses generic styling. |
| Edge labels in graph | Sample shows relationship labels on edges. Partial — edge labels shown but no path labels. |
| Search/filter nodes | No search by text content. |
| Batch path update | Can only edit one path at a time. |
| Undo/redo | No history. The sandbox NodeEditor has this — reuse that interaction. |
| Keyboard shortcuts | No shortcuts for save, navigate, collapse. |

---

## Portfolio / Global View

**Route**: `/`
**Current component**: `PortfolioPage.tsx`
**Sample reference**: `global_porfolio_view.html`

### What exists today

(Based on screenshot `01-portfolio-dashboard.png` — need to verify current implementation)

### Gaps vs. sample

| Gap | Description |
|---|---|
| Job status timeline | Sample shows horizontal pipeline timeline per job card. Current may show simple status. |
| Evidence bank summary | Sample shows skill tags and evidence count. Not implemented. |
| Application stats | Sample shows application history stats (submitted, rejected, pending). |
| Quick actions | Sample has "Apply", "Review", "Scrape" buttons per job. Current may lack these. |
| Search/filter jobs | Sample has search bar and filter chips. |

---

## Deployment View

**Route**: Not routed
**Sample reference**: `deployment.html`

### What exists today

Nothing. This is the **final stage**: package and submit.

### Sample describes

- Mission status panel (bundle complete / ready to submit)
- Final document preview (merged CV + motivation letter)
- Submission checklist (all reviews approved, all stages green)
- Bundle download button
- Submission log / history

---

## Design Decisions Already Made

1. **Palette + typography**: Fixed by samples. Do not redesign.
2. **Local-first**: All data lives in `data/jobs/`. No remote sync.
3. **JSON as source of truth**: UI edits map to JSON file writes. No separate DB.
4. **HitL review loop**: Operator must explicitly approve before pipeline continues.
5. **Minimal viable**: No speculative features. Every view must be functional.

---

## Open Questions for Designer

1. Should the Node Editor use the sandbox's full interaction model (focus mode, history, undo/redo)?
2. Is View 2's "inline requirement editing" a priority, or is the node editor flow acceptable?
3. How should the deployment view trigger the `package` pipeline stage — button in UI or CLI only?
4. Should evidence bank be a persistent sidebar across all job views, or only on Portfolio?
5. Is the current breadcrumb + tab navigation sufficient, or is a persistent sidebar nav preferred?
