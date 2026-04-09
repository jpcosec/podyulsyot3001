# Documentation

## Runtime
- `runtime/pipeline_overview.md` — generate_documents_v2 pipeline flow
- `runtime/data_management.md` — DataManager and artifact storage
- `runtime/review_ui.md` — Review UI (TUI) architecture and usage

## Standards

### docs/
Documentation, planning, navigation, and future work conventions.
- `standards/docs/documentation_and_planning_guide.md` — how to write READMEs, plan, and mark deferred work
- `standards/docs/documentation_quality_checklist.md` — evaluation checklist
- `standards/docs/future_docs_guide.md` — how to use `future_docs/`

### code/
Code quality standards by component type.
- `standards/code/basic.md` — universal: error contracts, LogTag, docstrings, CLI structure
- `standards/code/crawl4ai_usage.md` — how scraper code must use Crawl4AI, including bootstrap-via-LLM then converge-to-saved-schema
- `standards/code/llm_langgraph_components.md` — LangGraph module structure, node taxonomy, HITL contract, Studio pattern
- `standards/code/llm_langgraph_methodology.md` — build sequence, validation gates, test coverage contract
- `standards/code/ingestion_layer.md` — boundary ingestion: scraper, review input, future CV ingestion
