# UI vs. Dev State Integration Map

## Overview

| UI Stage / Concept | Info Source in dev | Gaps and Differences | UI Action / Strategy |
|--------------------|-------------------|---------------------|---------------------|
| 0. Portfolio / Dashboard | API: `GET /api/v1/portfolio/summary`<br>Mock: `fixtures/portfolio.json` | Aligned | Consume existing endpoint. Show states based on completed node folders. |
| 0. Evidence Tree (Base CV) | API: `CvProfileGraphPayload`, `CvEntry`, `CvSkill`<br>Mock: `cv_profile_graph.json` | Aligned | Paint skills/experience graph. Prepare side panel for drag & drop in Match. |
| 1. Scrape & Diagnostics | API: `GET /stage/scrape/outputs`<br>Files: `raw/source_text.md`, `trace/error_screenshot.png` | Aligned | Render text and show `<ErrorScreenshot />` if status indicates failure. |
| 3. Text Tagger (Extract) | API: `ViewTwoPayload` (`TextSpanItem`)<br>Mock: `view_extract_201397.json` | Data aligned, Flow gap | Render Tagger UI. On edit, PUT directly to `state.json` via Local Artifact Editor. |
| 4. Match & Evidence Inject | API: `GET /view1`, `GET /review/match`<br>Local: `feedback.json` via RoundManager | Aligned | Build Match Graph Canvas and Decision modal. Send comments/rejections to trigger regeneration loop. |
| 5.1. Strategy & Motivations | Code: `build_application_context` and `review_application_context` nodes in LangGraph | **CRITICAL GAP** - Nodes exist but bypassed (`PREP_MATCH_LINEAR_EDGES`) | Workaround: Design Motivations form, save as `strategy.json` via generic Explorer/Files API. |
| 5.2. Sculpt / Generation | Files: `nodes/generate_documents/proposed/*.md`<br>API: `useDocumentSave.ts` | Flow gap - Graph jumps to render without human review | Paint `DocumentTabs.tsx`. Overwrite markdown via API. Show "Force Render" button. |
| 8. Global Feedback Loop | Does not exist at global level | **CRITICAL GAP** - Feedback only for Match regeneration | Workaround: UI creates `ReviewNodes` in `data/jobs/.../review/` using generic file write endpoints. |

## Golden Rule: Local-First Superpower

Since the interface is a layer over the filesystem, UI has a "superpower" to avoid backend blocks:

### If backend doesn't stop at a stage (e.g., jumps from generate → render):

1. UI visually stops the user
2. UI retrieves generated files from `proposed/` (created lightning fast in background)
3. User edits calmly in the interface
4. UI uses `PUT /api/v1/jobs/{source}/{job_id}/documents/{doc_key}` to overwrite file
5. UI notifies backend: "Run only the Render node again using the files I just modified"

## Suggested Next Steps

With this map, UI developers can:

### Build NOW (endpoints and mocks 100% mapped)
- [ ] Scrape → Extract → Match (complete view)

### Leave as Mocks (save to Local Storage or raw files)
- [ ] Strategy (Motivations form)
- [ ] Global Feedback Loop

## Endpoint Reference

| Action | Endpoint |
|--------|----------|
| Portfolio summary | `GET /api/v1/portfolio/summary` |
| Scrape outputs | `GET /stage/scrape/outputs` |
| View extract | `GET /view2` |
| Match state | `GET /view1` |
| Review match | `GET /review/match` |
| Update match | `PATCH /review/match/evidence` |
| Save document | `PUT /api/v1/jobs/{source}/{job_id}/documents/{doc_key}` |
| Browse files | `GET /api/v1/jobs/{source}/{job_id}/browse` |
