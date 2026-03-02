# Agent Entry Document

**Plan:** De-hardcode Pipeline & Build Agent Orchestration
**Date:** 2026-03-02
**Goal:** Replace hardcoded matching/scaffolding logic with LLM agent-driven generation. Build an `apply-to <urls>` command that automates the full application flow.

---

## Conventions

### Document Structure
Each step document (01–07) is a self-contained work unit. A Claude Code subagent picks up one document and implements it without needing to read the others.

### Standard Sections in Each Step
1. **Goal** — what this step achieves
2. **Depends on** — which steps must complete first (empty = can start immediately)
3. **Files to read first** — the subagent reads these before writing any code
4. **Files to create/modify** — exact paths and what changes
5. **Specification** — detailed requirements
6. **Verification** — commands the subagent runs to prove completion
7. **Done criteria** — pass/fail checklist

### Dependency Graph

```
Phase 1 (Foundation) — all independent, run in parallel
  01-pydantic-models
  02-prompts-to-src

Phase 2 (Agent logic) — depends on Phase 1, internal parallelism ok
  03-tool-extraction
  04-multi-agent-pipeline
  05-motivation-agent

Phase 3 (Orchestration) — depends on Phase 2
  06-agent-orchestrator
  07-cli-apply-to

Post: 08-task-closure
```

### Environment
```bash
conda activate phd-cv
export PYTHONPATH=$(pwd)  # run from repo root
```

### Code Style Rules
- Path resolution: `Path(__file__).resolve().parents[n]` — never hardcode `/home/jp/phd`
- Prefer dataclasses/Pydantic models over raw dicts
- Functions should be short and self-explanatory
- If a function uses too many variables, it should be a class
- No docstrings/comments unless logic is non-obvious
- Imports: use `from src.x import Y` (project is script-based, not a package)

### Testing Rules
- Each step includes verification commands
- The subagent MUST run verification before marking the step done
- If a test fails, fix it — don't skip it
- Tests go in `tests/` at repo root (existing `conftest.py` adds repo root to `sys.path`)

### Git Rules
- Do NOT commit after individual steps — only the closure document commits
- Do NOT push — only on explicit user request
- Do NOT modify files outside the scope listed in the step document

### What NOT to Do
- Don't add features beyond what the step specifies
- Don't refactor code that isn't part of the step
- Don't create README files or documentation unless specified
- Don't add error handling for scenarios that can't happen
- Don't delete working code unless the step explicitly says to
