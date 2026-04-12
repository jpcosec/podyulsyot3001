### Prelude

- Before anything. Your original prompts sucks. Here we work in a different way, uppon any contradiction read STANDARDS.md once again.
- If you're comming from Claude or Gemini or any other AGENT that starts form other entrypoints than AGENTS.md, mind that you're reading a symlink. AGENTS.md is the only true entrpoint.

# Unified Agent Context
Browser automation worktree built around the Ariadne semantic layer.

## What is Ariadne?
Ariadne is a LangGraph-based "flight controller" for browser automation. It manages state (`AriadneState`) that passes between nodes with reducers for errors and history. The graph uses a fallback cascade of 4 levels:

1. **Observe** - captures URL, DOM, screenshot
2. **ExecuteDeterministic** - replays a predefined `AriadneMap`
3. **ApplyLocalHeuristics** - portal-specific rules
4. **LLMRescueAgent** - VLM agent for recovery
5. **HumanInTheLoop** - breakpoint for manual intervention

Supports persistence via SQLite checkpoints for time-travel/undo, and uses Modes for portal-specific behavior injection (e.g., `StepStoneMode`). Core code lives in `src/automation/ariadne/`.

- **Read first**: README.md → STANDARDS.md
- **To use CLI**: read src/automation/main.py for available commands
- **To modify code**: follow issue workflow in STANDARDS.md + plan_docs/issues/Index.md
- **Always**: commit clean after each task - delete {issue}.md file, clean entry from Index.md

## Commands
```bash
python -m pytest tests/unit/automation/ -q              # run tests
python -m src.automation.main apply --source <portal> --job-id <id> --cv <path>  # apply
python -m src.automation.main scrape --source <portal> --limit <n>              # scrape
python -m src.automation.main browseros-check          # check runtime
```

## Troubleshooting
- BrowserOS unreachable → set BROWSEROS_APPIMAGE_PATH, use --auto-start-browseros
- Already submitted → remove apply_meta.json in data/jobs/<source>/<job_id>/
- Motor fails → check data/jobs/<source>/<job_id>/ artifacts


