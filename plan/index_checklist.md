# Planning Checklist

This is the single planning checklist for active work.

## 01 UI — Phase 1: Minimal JSON Editor

- [x] Job page as hub of navigation
- [x] Pipeline outputs view (inspect by stage)
- [x] NodeEditor for extract_understand
- [x] NodeEditor for match
- [x] Document editing for generate_documents
- [x] Scrape diagnostics view with screenshots
- [x] NodeEditor sandbox patterns: undo/redo, focus mode, search, keyboard shortcuts
- [x] View 3 document sculpting (editable, word count, contrast diff)
- [x] Deployment view (basic routing + package status)

## 02 AI — Phase 1: LLM Wrappers and Structured Output

- [x] ChatGoogleGenerativeAI.with_structured_output() for extract_understand
- [x] contact_info stable extraction
- [x] salary_grade strictly optional
- [x] Deterministic TextSpan via resolve_span (no LLM offsets)
- [x] LangSmith structured config (LLMConfig + trace_section)
- [x] LangSmith traces for extract_understand and match stages

## 03 Scrapper — Phase 1: Robust Scraping and Auto-Apply

- [x] PlaywrightFetcher with try/except
- [x] error_screenshot.png on failures
- [x] bot_profile persistent directory
- [x] HTTP -> Playwright -> LLM fallback cascade
- [x] Artifacts under nodes/scrape/ and raw/source_text.md
- [x] Visible mode used and warnings in UI

## Rules

- Mark a phase complete only when code, verification, and changelog agree.
- Archive obsolete planning docs instead of letting them drift in active folders.
- Put subsystem specs in `docs/`, not in `plan/`.

## Completion Criteria (from minimal_viable_architecture_completion_plan.md)

All 12 criteria met as of dev:

1. [x] extract_understand and match load/edit/save from UI
2. [x] generate_documents reviewed and edited from UI
3. [x] Job page inspects outputs per stage
4. [x] extract_understand uses LangChain wrappers (fail-closed intact)
5. [x] LangSmith traces main stages (structured config)
6. [x] contact_info stable
7. [x] salary_grade strictly optional
8. [x] TextSpan determinista (resolve_span service)
9. [x] PlaywrightFetcher saves error_screenshot.png
10. [x] HTTP -> Playwright -> LLM cascade auditable
11. [x] No Neo4j added
12. [x] data/jobs/ sole source of truth
