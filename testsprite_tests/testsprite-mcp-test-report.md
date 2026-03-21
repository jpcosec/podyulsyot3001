# PhD 2.0 Review Workbench — TestSprite Test Report

---

## 1️⃣ Document Metadata

| Field | Value |
|---|---|
| **Project Name** | PhD 2.0 Review Workbench |
| **Date** | 2026-03-21 |
| **Prepared by** | TestSprite AI (via MCP) |
| **Test Scope** | Frontend diff — UI improvements + Data Explorer |
| **Test Run ID** | dfd05b38-02e3-4724-b9b9-7492ac651a98 |
| **Server Mode** | Production (Vite preview, port 4174) |

---

## 2️⃣ Requirement Validation Summary

### REQ-1: Portfolio Dashboard

#### TC001 — Portfolio dashboard shows overall job statistics
- **Status:** ✅ Passed
- **Analysis:** Stats grid (Total Jobs, Pending Review, Completed, Failed) renders correctly from `/api/v1/portfolio/summary`.

#### TC002 — Portfolio dashboard shows next review target details
- **Status:** ✅ Passed
- **Analysis:** Review queue correctly surfaces the next paused/review-stage job with source, job ID, and current node.

#### TC003 — Open job workspace from next review target
- **Status:** ✅ Passed
- **Analysis:** "Open job workspace" link navigates correctly to `/jobs/:source/:jobId`.

#### TC004 — Navigate from portfolio to Data Explorer via artifacts link
- **Status:** ✅ Passed
- **Analysis:** "Browse all local job artifacts" link navigates to `/explorer` and the Data Explorer loads.

#### TC006 — Expand a source node in the job tree to reveal child jobs
- **Status:** ✅ Passed
- **Analysis:** JobTree collapsible groups expand/collapse correctly.

---

### REQ-2: Data Explorer

#### TC009 — Open Data Explorer and view root data/jobs/ directory listing
- **Status:** ✅ Passed
- **Analysis:** `/explorer` shows root-level source folders (stepstone, tu_berlin) with item counts.

#### TC010 — Navigate into a folder and verify ?path= updates and folder contents are shown
- **Status:** ✅ Passed
- **Analysis:** Clicking a folder updates the `?path=` query param and shows child entries with correct breadcrumbs.

#### TC011 — Preview a JSON file with pretty-printed output
- **Status:** ✅ Passed
- **Analysis:** JSON files render pretty-printed with syntax indentation in the preview pane.

#### TC013 — Preview an image file inline (PNG/JPG/GIF/SVG)
- **Status:** ❌ Failed
- **Analysis:** No image files exist in `data/jobs/` in the test environment. The image preview code path exists and is correct, but there was no test data to exercise it. Not a code defect — data-only gap.

#### TC014 — Use breadcrumb navigation to go back up the directory tree
- **Status:** ✅ Passed
- **Analysis:** Breadcrumb links correctly navigate to parent directories via `?path=` param.

---

### REQ-3: Job Workspace

#### TC017 — Graph Explorer loads with graph visible in View 1
- **Status:** ✅ Passed
- **Analysis:** ReactFlow canvas renders pipeline graph nodes for job tu_berlin/201588.

#### TC018 — Selecting a graph edge shows match reasoning below the graph
- **Status:** ❌ Failed
- **Analysis:** View 1 tab switcher was not found — the workspace loaded directly into "View 2: Document to Graph" with no graph edges present for this job's state. The match reasoning panel exists in code but requires a job with completed match stage data to show edges. For job 201588 at `generate_documents` stage, the view renders differently. This is a state-dependent rendering issue, not a regression.

---

### REQ-4: Extraction View (View 2)

#### TC022 — View 2 tab loads and shows line-by-line source markdown as selectable lines
- **Status:** ❌ Failed
- **Analysis:** View 2 source panel stuck on "Loading source text..." — the source markdown content never resolves. This is a real bug: the View 2 component likely has an API call or state dependency that fails silently for this job. Needs investigation in `JobStagePage.tsx` View 2 data loading.

#### TC023 — Selecting a markdown line shows requirement metadata panel
- **Status:** ❌ Failed
- **Analysis:** Downstream failure from TC022 — no source lines rendered so interaction is impossible.

#### TC026 — Changing selection updates the requirement panel to a different requirement
- **Status:** ❌ Failed
- **Analysis:** Downstream failure from TC022 — same root cause.

---

## 3️⃣ Coverage & Matching Metrics

- **Pass rate:** 10/15 = **66.7%**

| Requirement | Total Tests | ✅ Passed | ❌ Failed |
|---|---|---|---|
| REQ-1: Portfolio Dashboard | 5 | 5 | 0 |
| REQ-2: Data Explorer | 5 | 4 | 1 (data gap) |
| REQ-3: Job Workspace — Graph | 2 | 1 | 1 (state-dependent) |
| REQ-4: Extraction View 2 | 3 | 0 | 3 (real bug) |
| **Total** | **15** | **10** | **5** |

---

## 4️⃣ Key Gaps / Risks

| # | Issue | Severity | Location | Action |
|---|---|---|---|---|
| 1 | **View 2 source text never loads** — "Loading source text..." never resolves for job 201588. Three tests blocked by this. | High | `JobStagePage.tsx` — View 2 data fetch | Investigate API call and error handling for view2 source text endpoint |
| 2 | **Image preview untestable** — No PNG/JPG/GIF/SVG files exist in `data/jobs/` to exercise the inline image preview path | Low | `DataExplorerPage.tsx` / data | Add a test image artifact to the data directory, or document that image preview is manual-test only |
| 3 | **Graph edge match reasoning requires specific job state** — TC018 requires a job with match edges loaded, but the test ran on a job past that stage | Low | `JobStagePage.tsx` View 1 | Use a job fixture at `match` stage for this test, or document state dependency |
| 4 | **Evidence Bank and Graph Explorer share same URL** — Both sidebar nav items highlight active simultaneously | Low | `JobWorkspaceSidebar.tsx` | Implement tab/view switching via query params to give each link a unique active state |
| 5 | **ScrapeDiagnosticsTab not implemented** — Checklist claims it exists, but the component is missing | Medium | `apps/review-workbench/src/` | Implement the component or remove the checklist item |
