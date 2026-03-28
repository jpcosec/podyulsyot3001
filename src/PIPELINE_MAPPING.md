# Pipeline Mapping: Old Dev → New LangGraph

This document maps the old `src/nodes/*` pipeline to the new LangGraph-native modules.

---

## Old Pipeline (dev branch)

```
scrape
  ↓
translate_if_needed
  ↓
extract_understand
  ↓
match
  ↓
review_match ──(approve)──→ build_application_context ──(approve)──→ generate_documents
  │                              ↓                                     ↓
  ├──(reject)                  review_application_context         generate_motivation_letter
  │                              ↓                                     ↓
  └──(regen)                  review_motivation_letter           review_cv
                                 ↓                                     ↓
                              generate_documents ──(approve)──→ tailor_cv ──(approve)──→ draft_email
                                                                         ↓
                                                                     review_email
                                                                         ↓
                                                                       render
                                                                         ↓
                                                                     package
```

---

## New Structure

| Old Node | New Module | Purpose |
|----------|-----------|---------|
| `scrape` | `src/scraper/` | Job posting scraping |
| `translate_if_needed` | `src/tools/translator/` | Field/document translation |
| `extract_understand` | *(scraper output)* | LLM extraction from scraped HTML |
| `match` | `src/match_skill/` | **LangGraph** - Requirement matching with HITL |
| `review_match` | `src/match_skill/` + `src/review_ui/` | Human review breakpoint + TUI |
| `build_application_context` | *(inside match_skill)* | Builds approved match payload |
| `generate_documents` | `src/generate_documents/` | **LangGraph** - CV/letter/email generation |
| `render` | `src/tools/render/` | **Deterministic** - Pandoc + Jinja2 → PDF/DOCX |
| `package` | *(manual)* | Bundles outputs for submission |

---

## Module Details

### `src/match_skill/` (LangGraph)
- **Replaces:** `match` + `review_match` + `build_application_context`
- **Graph:** `match_skill` (exposed via `langgraph.json`)
- **Features:**
  - LLM matching with structured output
  - Breakpoint at `human_review_node`
  - Immutable round artifacts
  - Studio-integrated
- **Artifacts:** `output/match_skill/<source>/<job_id>/nodes/match_skill/`

### `src/generate_documents/` (LangGraph)
- **Replaces:** `generate_documents` (simplified)
- **Graph:** `generate_documents` (exposed via `langgraph.json`)
- **Features:**
  - Reads approved matches from `match_skill`
  - LLM structured output → Jinja2 templates
  - Deterministic review indicators
- **Artifacts:** `output/match_skill/<source>/<job_id>/nodes/generate_documents/`

### `src/tools/render/` (Deterministic)
- **Replaces:** `render`
- **Engine:** Pandoc + Jinja2 + LaTeX
- **Supports:** PDF, DOCX
- **Documents:** CV, Cover Letter
- **Entry:** `RenderCoordinator` in `coordinator.py`

### `src/tools/translator/` (Deterministic)
- **Replaces:** `translate_if_needed`
- **Provider:** Google Translate API
- **Entry:** `translate_text()`, `translate_document()`

### `src/scraper/`
- **Replaces:** `scrape` + `extract_understand`
- **Adapters:** Generic, Stepstone, Xing
- **Output:** `JobPosting` Pydantic models

### `src/review_ui/`
- **Replaces:** Review TUI components
- **Framework:** Textual
- **Entry:** `MatchReviewApp`

---

## Running the Pipeline

### Via LangGraph Studio
```
http://127.0.0.1:8124
Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8124
```

### Via API
```bash
# 1. Run match_skill
curl -X POST "http://127.0.0.1:8124/threads/<thread_id>/runs" \
  -d '{"assistant_id": "<match_skill_id>", "input": {...}}'

# 2. After approval, run generate_documents
curl -X POST "http://127.0.0.1:8124/threads/<thread_id>/runs" \
  -d '{"assistant_id": "<generate_documents_id>", "input": {...}}'

# 3. Render to PDF
python -m src.tools.render.main cv --source <deltas.json> --language en
```

---

## Key Differences

| Aspect | Old (dev) | New |
|--------|-----------|-----|
| Framework | Custom LangGraph + markdown files | Native LangGraph + JSON artifacts |
| State | `GraphState` dict | TypedDict + checkpointing |
| Review | Markdown file editing | TUI + Studio |
| Documents | LaTeX directly | Jinja2 → Pandoc → PDF |
| Studio | Not integrated | Full support |
| CLI | Multiple scripts | Removed (use API/Studio) |
