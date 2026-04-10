# Documentation

## Automation system

- `automation/README.md` — index: implementation references and applicable standards
- `automation/architecture.md` — design rationale, Ariadne boundary, motor separation, scrape and apply data flows

## Standards

### docs/
Documentation, planning, and navigation conventions for this scoped worktree.
- `standards/docs/documentation_and_planning_guide.md` — how to write READMEs, plan, and mark deferred work
- `standards/docs/documentation_quality_checklist.md` — evaluation checklist

### code/
Code quality standards by component type.
- `standards/code/basic.md` — universal: error contracts, LogTag, docstrings, CLI structure
- `standards/code/crawl4ai_usage.md` — how scraper code must use Crawl4AI, including bootstrap-via-LLM then converge-to-saved-schema
- `standards/code/ingestion_layer.md` — boundary ingestion rules for scraper-facing inputs in this worktree
