# Documentation

## Standards

### docs/
Documentation, planning, and navigation conventions for this scoped worktree.
- `standards/docs/documentation_and_planning_guide.md` — how to write READMEs, plan, and mark deferred work
- `standards/docs/documentation_quality_checklist.md` — evaluation checklist

### code/
Code quality standards by component type.
- `standards/code/basic.md` — universal: error contracts, LogTag, docstrings, CLI structure
- `standards/code/crawl4ai_usage.md` — how scraper code must use Crawl4AI, including bootstrap-via-LLM then converge-to-saved-schema
- `standards/code/llm_langgraph_components.md` — LangGraph module structure, node taxonomy, HITL contract, Studio pattern
- `standards/code/llm_langgraph_methodology.md` — build sequence, validation gates, test coverage contract
- `standards/code/ingestion_layer.md` — boundary ingestion rules for scraper-facing inputs in this worktree
