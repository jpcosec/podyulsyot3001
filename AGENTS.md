# AGENTS.md — Unified Agent Context

This is the canonical agent entrypoint for this repository.
`CLAUDE.md` and `GEMINI.md` should be compatibility symlinks to this file so all agents read the same project guidance.

WARNING: if you opened `CLAUDE.md` or `GEMINI.md`, you are reading a symlinked compatibility path. The real source of truth is `AGENTS.md`. Edit `AGENTS.md` only.

## Project Orientation

This repository is a browser-automation worktree built around the Ariadne semantic layer.
Agents should orient first, then execute: understand the architecture, verify runtime prerequisites, follow the issue workflow, and only then make code or documentation changes.

- Read `README.md` first for repository shape and purpose.
- For code or documentation edits, follow `STANDARDS.md` instead of relying on local habits.
- Treat `src/automation/main.py` as the main CLI entrypoint for automation flows.
- Treat `plan_docs/issues/Index.md` as the execution queue once issue planning is active.
- For deep context on the architecture and state graph, read the specifications in `docs/ariadne/`.

## Runtime Prerequisite

BrowserOS must be launched before using any BrowserOS-backed flow or validation.
Do not assume the runtime is already available.

```bash
export BROWSEROS_APPIMAGE_PATH="/path/to/BrowserOS.AppImage"
"$BROWSEROS_APPIMAGE_PATH" --no-sandbox
curl http://127.0.0.1:9000/mcp
```

- Launch BrowserOS before `apply`, BrowserOS-backed `scrape`, `browseros-check`, or BrowserOS recording/promotion work.
- Prefer `http://127.0.0.1:9000` as the stable local front door.
- Override with `BROWSEROS_BASE_URL`.

## Common Commands

```bash
# Run all automation unit tests
python -m pytest tests/unit/automation/ -q

# Run a specific test file
python -m pytest tests/unit/automation/ariadne/test_orchestrator.py -v

# Scrape jobs from a portal
python -m src.automation.main scrape --source <stepstone|xing|tuberlin> --limit <n>

# Scrape with visible collaborative recording
python -m src.automation.main scrape --interactive --visible --record --backend browseros --source <portal> --limit <n>

# Apply to a job (BrowserOS default motor)
python -m src.automation.main apply --source <xing|stepstone|linkedin> --job-id <id> --cv <path>

# Apply via Crawl4AI backend
python -m src.automation.main apply --backend crawl4ai --source <portal> --job-id <id> --cv <path>

# Dry-run apply (no submission)
python -m src.automation.main apply --source <portal> --job-id <id> --cv <path> --dry-run

# Verify BrowserOS runtime
python -m src.automation.main browseros-check
```

## BrowserOS Runtime

BrowserOS is an external AppImage, not a Python service in this repo.

| Endpoint | Default |
| --- | --- |
| Base | `http://127.0.0.1:9000` |
| MCP | `http://127.0.0.1:9000/mcp` |
| Chat | `http://127.0.0.1:9000/chat` |

## Architecture

The system uses the Ariadne Semantic Layer to decouple portal logic from execution engines. The architecture revolves around a state graph.

### Key Layers

**`src/automation/ariadne/`** — backend-neutral brain:
- `models.py`: core types including `AriadnePortalMap`, `AriadneState`, `AriadneStep`, etc.
- `graph/`: contains state machine orchestrator (`orchestrator.py`) and agent nodes.
- `modes/`: execution modes (e.g., `default.py`).
- `translators/`: normalizers and translators for BrowserOS and Crawl4ai.
- `capabilities/`: tools for the pipeline such as hinting capabilities.
- `danger_contracts.py`: pre-submit safety guards.

**`src/automation/portals/`** — portal maps and routing:
- `<portal>/maps/easy_apply.json`: canonical apply flow map.
- `configs/`: portal specific and system configurations.

**`src/automation/motors/`** — execution backends:
- `browseros/executor.py`: MCP-driven execution with fuzzy text targeting.
- `crawl4ai/executor.py`: Crawl4AI execution engine.

**`src/automation/`** root:
- `main.py`: CLI dispatcher for `scrape`, `apply`, `browseros-check`, and `promote`.
- `contracts.py`: shared execution payloads.

## Development Principles

1. Ariadne first: new portals and flows start as `AriadnePortalMap` JSON, not motor-specific code.
2. Backend neutrality: actions use `AriadneIntent`; targets carry both `css` and `text` when possible.
3. State-driven recovery: use `AriadneState` selectors so navigation can recover from drift.
4. Normalization ownership: semantic cleanup belongs in `src/automation/ariadne/translators/`, not in individual motor executors.
5. Multi-stage artifacts: scrape outputs flow through `raw.json`, `cleaned.json`, and `extracted.json` under `data/jobs/<source>/<job_id>/`.

## Standards First

When editing code or documentation, refer to `STANDARDS.md` before making changes.

- Code standards start at `STANDARDS.md`.
- Documentation and planning standards start at `STANDARDS.md`.
- Issue planning and execution rules live in `STANDARDS.md`.
- `README.md` is the top-level human entrypoint; general docs belong under `docs/`; module-specific docs belong near the module they describe.
- Record every major change in `changelog.md`.

## Testing Guidelines

- Tests live in `tests/unit/automation/` mirroring `src/`.
- Use `pytest` naming conventions: `test_*.py` and `test_*` functions.
- Add regression coverage for behavior changes, especially portal maps, routing, normalization, and motor adapters.

## Issue And Design Cycle

- Every change is managed through `STANDARDS.md`.
- Planning artifacts live under `plan_docs/issues/`.
- `plan_docs/issues/Index.md` is the issue entrypoint and active dependency index.
- The correct order of execution is: atomization of issues, contradiction checking, then prioritization via dependencies.
- During contradiction checking: if an issue is legacy, delete it; if issues contradict each other, resolve the contradiction or ask the user only when a real design decision is required.
- Never ask the user which issue to solve next; there is no usefulness in that. Follow dependency order from `plan_docs/issues/Index.md`.
- Do not ask the user for permission to continue to the next protocol-defined step. If the dependency order, issue workflow, and git-safety rules already determine the next action, just do it.
- Do not ask rhetorical progress questions such as whether to continue, whether to take the next cleanup step, or whether to make the required snapshot commit.

### Execution Mandates

To ensure system integrity and agent efficiency, follow the **Commit -> Delete -> Clean** cycle:

1.  **Granular Traceability**: Commit immediately after solving a single atomized issue. This creates a perfect audit log and allows for surgical reverts if a regression is introduced.
2.  **Ephemerality**: Issue files are temporary work contracts. Once the work is delivered and verified, **delete the issue file** immediately. Leaving fulfilled contracts in the workspace violates the "no archives" rule.
3.  **Context Integrity**: For AI agents, a finished task remaining in the `Index.md` is "noise" that consumes context and causes redundant reasoning. **Remove resolved entries from the Index** to maintain focus on the next dependency.
4.  **Single Source of Truth**: The `Index.md` must always reflect the *live* state of the project. If an entry is present, the logic must be physically missing or broken in the code.

## Documentation Lifecycle

- Planning happens in `plan_docs/issues/`.
- `session-ses_*.md` files are old conversation traces; absorb anything useful into canonical docs/issues and delete the trace when it no longer adds value.
- When a feature tracked in `plan_docs/` is fully implemented, make sure the implementation and documentation have absorbed the needed knowledge, then delete the finished planning artifact.

## Git Hygiene

- Never edit anything while the git tree is dirty.
- First make a commit with the existing untracked or unstaged work, then edit on top of that clean state.
- Do this automatically; do not ask the user whether to make the snapshot commit just to satisfy git cleanliness.
- Do not overwrite or discard user work to create cleanliness.

## Key References

- `README.md`
- `STANDARDS.md`
- `docs/ariadne/architecture_and_graph.md`
- `docs/ariadne/execution_interfaces.md`
- `docs/ariadne/fitness_functions.md`
- `docs/ariadne/portals_and_modes.md`
- `docs/ariadne/recording_and_promotion.md`

## Troubleshooting

- `BrowserOS unreachable`: set `BROWSEROS_APPIMAGE_PATH`, launch `"$BROWSEROS_APPIMAGE_PATH" --no-sandbox`, and verify `http://127.0.0.1:9000/mcp`.
- `RuntimeError: already submitted`: inspect or remove the relevant `apply_meta.json` in the job artifact directory if you intentionally need a fresh run.
- `Motor failures`: inspect preserved job artifacts under `data/jobs/`.